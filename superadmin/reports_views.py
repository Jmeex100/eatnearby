from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.utils.timezone import now, localtime
from django.http import JsonResponse
from django.conf import settings
from django import forms
from auths.models import User, FastFood, Food, Drink
from payments.models import PaymentHistory, DeliveryInfo
from cart.models import Cart, CartItem
from staffs.models import StaffAssignment
from community.models import Review
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
import datetime
from datetime import timedelta
import json
from collections import defaultdict
import os
# superadmin/reports_views.py
# Enhanced Filter Form
class AnalyticsFilterForm(forms.Form):
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Date Range')
    ]
    
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES, required=False, initial='this_month', label="Date Range")
    date_start = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'date-input'}), label="Start Date")
    date_end = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'date-input'}), label="End Date")
    user_type = forms.ChoiceField(choices=[('', 'All Users'), ('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')], required=False, label="User Type")
    min_sales = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'e.g., 100'}), label="Minimum Sales Amount (K)")
    max_sales = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'e.g., 1000'}), label="Maximum Sales Amount (K)")
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search transactions, users, products...'}), label="Search")
    report_type = forms.MultipleChoiceField(
        choices=[('sales', 'Sales Reports'), ('users', 'User Reports'), ('inventory', 'Inventory Reports'), ('staff', 'Staff Performance'), ('customer', 'Customer Satisfaction')],
        required=False, widget=forms.CheckboxSelectMultiple, label="Report Types"
    )

@login_required
def generate_pdf_report(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=30, textColor=colors.HexColor('#1f2937'))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=12, textColor=colors.HexColor('#374151'))
    subheading_style = ParagraphStyle('CustomSubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6, textColor=colors.HexColor('#4b5563'))
    normal_style = styles['BodyText']
    small_style = ParagraphStyle('SmallText', parent=styles['BodyText'], fontSize=8)

    # Header with logo
    logo_path = os.path.join(getattr(settings, 'STATIC_ROOT', ''), 'img', 'logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.5*inch, height=0.75*inch))
    
    elements.append(Paragraph("EATNEAR-BY ANALYTICS DASHBOARD REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {localtime(now()).strftime('%Y-%m-%d %H:%M')}", normal_style))
    
    # Display applied filters
    form = AnalyticsFilterForm(request.GET)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        date_range = form.cleaned_data.get('date_range')
        user_type = form.cleaned_data.get('user_type')
        min_sales = form.cleaned_data.get('min_sales')
        max_sales = form.cleaned_data.get('max_sales')
        query = form.cleaned_data.get('query')
        report_types = form.cleaned_data.get('report_type', [])
        
        filter_text = "Filters Applied: "
        filters = []
        if date_range and date_range != 'custom':
            filters.append(f"Period: {dict(form.fields['date_range'].choices)[date_range]}")
        if date_start:
            filters.append(f"From: {date_start}")
        if date_end:
            filters.append(f"To: {date_end}")
        if user_type:
            filters.append(f"User Type: {user_type.capitalize()}")
        if min_sales:
            filters.append(f"Min Sales: K{min_sales}")
        if max_sales:
            filters.append(f"Max Sales: K{max_sales}")
        if query:
            filters.append(f"Search: '{query}'")
        if report_types:
            type_names = [dict(form.fields['report_type'].choices).get(t, t) for t in report_types]
            filters.append(f"Report Types: {', '.join(type_names)}")
        
        filter_text += ", ".join(filters) if filters else "None"
        elements.append(Paragraph(filter_text, normal_style))
    
    elements.append(Spacer(1, 0.25 * inch))

    report_data = get_enhanced_report_data(form.cleaned_data if form.is_valid() else {})

    # Executive Summary
    elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    summary = report_data['summary']
    summary_data = [
        ["Metric", "Value", "Comparison", "Trend"],
        ["Total Revenue", f"K{summary['total_revenue']:,.2f}", f"{summary['revenue_growth']}% vs previous", "📈" if summary['revenue_growth'] > 0 else "📉"],
        ["Total Orders", f"{summary['total_orders']:,}", f"{summary['orders_growth']}% vs previous", "📈" if summary['orders_growth'] > 0 else "📉"],
        ["Average Order Value", f"K{summary['avg_order_value']:,.2f}", f"{summary['aov_growth']}% vs previous", "📈" if summary['aov_growth'] > 0 else "📉"],
        ["New Customers", f"{summary['new_customers']:,}", f"{summary['customer_growth']}% vs previous", "📈" if summary['customer_growth'] > 0 else "📉"],
        ["Customer Satisfaction", f"{summary['avg_rating']:.1f}/5", "Based on reviews", "⭐" * int(round(summary['avg_rating']))],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 2*inch, 0.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbeb')]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Sales Chart
    if report_data['charts'].get('sales_trend'):
        elements.append(Paragraph("SALES TREND", heading_style))
        drawing = Drawing(400, 200)
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 125
        bc.width = 300
        bc.data = [report_data['charts']['sales_trend']['values']]
        bc.strokeColor = colors.white
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = max(report_data['charts']['sales_trend']['values']) * 1.1 if report_data['charts']['sales_trend']['values'] else 100
        bc.categoryAxis.categoryNames = report_data['charts']['sales_trend']['labels']
        bc.bars[0].fillColor = colors.HexColor('#f59e0b')
        drawing.add(bc)
        elements.append(drawing)
        elements.append(Spacer(1, 0.25 * inch))
    else:
        elements.append(Paragraph("SALES TREND: No data available", heading_style))
        elements.append(Spacer(1, 0.25 * inch))

    # Top Products
    if report_data['detailed_reports'].get('top_products'):
        elements.append(Paragraph("TOP SELLING PRODUCTS", heading_style))
        top_products_data = [["Product", "Category", "Units Sold", "Revenue", "% of Total"]]
        for product in report_data['detailed_reports']['top_products']:
            top_products_data.append([
                product['name'][:30] + '...' if len(product['name']) > 30 else product['name'],
                product['category'],
                f"{product['units_sold']:,}",
                f"K{product['revenue']:,.2f}",
                f"{product['percentage']:.1f}%"
            ])
        
        top_products_table = Table(top_products_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 1*inch, 0.7*inch])
        top_products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(top_products_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Monthly Sales
    elements.append(Paragraph("MONTHLY SALES PERFORMANCE", heading_style))
    monthly_sales_data = [["Month", "Total Sales", "Transactions", "Avg. Order Value", "Growth"]]
    for item in report_data['summary_reports']['monthly_sales']:
        growth = item.get('growth')
        growth_symbol = "▲" if growth and growth > 0 else "▼" if growth and growth < 0 else "➖"
        # growth_color = colors.green if growth and growth > 0 else colors.red if growth and growth < 0 else colors.gray
        monthly_sales_data.append([
            item['month'],
            f"K{item['total_sales']:,.2f}",
            f"{item['transaction_count']:,}",
            f"K{item.get('avg_order_value', 0):,.2f}",
            f"{growth_symbol} {abs(growth):.1f}%" if growth is not None else "N/A"
        ])
    
    monthly_sales_table = Table(monthly_sales_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch])
    monthly_sales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        # ('TEXTCOLOR', (-1, 1), (-1, -1), growth_color),
    ]))
    elements.append(monthly_sales_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Staff Performance
    if report_data['summary_reports'].get('staff_performance'):
        elements.append(Paragraph("STAFF PERFORMANCE", heading_style))
        staff_performance_data = [["Staff", "Total Deliveries", "Completed", "Completion Rate"]]
        for item in report_data['summary_reports']['staff_performance']:
            staff_performance_data.append([
                item['username'],
                f"{item['total_deliveries']:,}",
                f"{item['completed_deliveries']:,}",
                f"{item['completion_rate']:.1f}%"
            ])
        
        staff_table = Table(staff_performance_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
        staff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
        ]))
        elements.append(staff_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Customer Satisfaction
    elements.append(Paragraph("CUSTOMER SATISFACTION", heading_style))
    customer_satisfaction = report_data['summary_reports'].get('customer_satisfaction', {})
    customer_satisfaction_data = [
        ["Metric", "Rating", "Trend"],
        ["Overall Rating", f"{customer_satisfaction.get('average_rating', 0):.1f}/5", "⭐" * int(round(customer_satisfaction.get('average_rating', 0)))],
        ["Food Rating", f"{customer_satisfaction.get('average_food_rating', 0):.1f}/5", "⭐" * int(round(customer_satisfaction.get('average_food_rating', 0)))],
        ["Service Rating", f"{customer_satisfaction.get('average_service_rating', 0):.1f}/5", "⭐" * int(round(customer_satisfaction.get('average_service_rating', 0)))],
        ["Ambiance Rating", f"{customer_satisfaction.get('average_ambiance_rating', 0):.1f}/5", "⭐" * int(round(customer_satisfaction.get('average_ambiance_rating', 0)))],
    ]
    
    customer_satisfaction_table = Table(customer_satisfaction_data, colWidths=[1.5*inch, 1*inch, 2*inch])
    customer_satisfaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
    ]))
    elements.append(customer_satisfaction_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Recent Reviews
    if report_data['detailed_reports'].get('recent_reviews'):
        elements.append(Paragraph("RECENT CUSTOMER REVIEWS", heading_style))
        for i, review in enumerate(report_data['detailed_reports']['recent_reviews'][:5]):
            review_text = f"\"{review['comment'][:100]}{'...' if len(review['comment']) > 100 else ''}\""
            elements.append(Paragraph(f"Review by {review['user']} ({review['rating']}/5):", subheading_style))
            elements.append(Paragraph(review_text, normal_style))
            elements.append(Paragraph(f"Date: {review['date']}", small_style))
            if i < len(report_data['detailed_reports']['recent_reviews'][:5]) - 1:
                elements.append(Spacer(1, 0.1 * inch))

    # High-Value Orders
    if report_data['exception_reports'].get('high_value_orders'):
        elements.append(Paragraph("HIGH VALUE ORDERS (>K100)", heading_style))
        high_value_data = [["Transaction ID", "Customer", "Amount", "Date"]]
        for order in report_data['exception_reports']['high_value_orders']:
            high_value_data.append([
                order['transaction_id'],
                order['user'],
                f"K{order['total']:,.2f}",
                order['created_at'].strftime('%Y-%m-%d')
            ])
        
        high_value_table = Table(high_value_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch])
        high_value_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(high_value_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Low Inventory
    if report_data['exception_reports'].get('low_inventory'):
        elements.append(Paragraph("LOW INVENTORY ITEMS (<10)", heading_style))
        low_inventory_data = [["Product ID", "Name", "Category", "Quantity"]]
        for item in report_data['exception_reports']['low_inventory']:
            low_inventory_data.append([
                str(item['product_id']),
                item['name'],
                item['category'],
                f"{item['quantity']:,}"
            ])
        
        low_inventory_table = Table(low_inventory_data, colWidths=[1*inch, 1.5*inch, 1*inch, 0.8*inch])
        low_inventory_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(low_inventory_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Footer
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Confidential - For Internal Use Only", small_style))
    elements.append(Paragraph(f"Report generated by {request.user.get_full_name() or request.user.username}", small_style))

    doc.build(elements)
    response = HttpResponse(content_type='application/pdf')
    filename = f"foodle_analytics_report_{now().strftime('%Y%m%d_%H%M')}.pdf"
    disposition = 'attachment' if request.GET.get('download', '').lower() == 'true' else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    buffer.seek(0)
    response.write(buffer.read())
    buffer.close()
    return response

def get_enhanced_report_data(filters=None):
    if filters is None:
        filters = {}

    # Determine date range
    date_range = filters.get('date_range', 'this_month')
    today = now().date()
    
    if date_range == 'today':
        date_start = today
        date_end = today
    elif date_range == 'yesterday':
        date_start = today - timedelta(days=1)
        date_end = today - timedelta(days=1)
    elif date_range == 'this_week':
        date_start = today - timedelta(days=today.weekday())
        date_end = today
    elif date_range == 'last_week':
        date_start = today - timedelta(days=today.weekday() + 7)
        date_end = date_start + timedelta(days=6)
    elif date_range == 'this_month':
        date_start = today.replace(day=1)
        date_end = today
    elif date_range == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_month_end = first_day_this_month - timedelta(days=1)
        date_start = last_month_end.replace(day=1)
        date_end = last_month_end
    elif date_range == 'this_quarter':
        quarter = (today.month - 1) // 3 + 1
        date_start = datetime.date(today.year, 3 * quarter - 2, 1)
        date_end = min(today, datetime.date(today.year, 3 * quarter, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif date_range == 'this_year':
        date_start = datetime.date(today.year, 1, 1)
        date_end = today
    else:
        date_start = filters.get('date_start') or today.replace(day=1)
        date_end = filters.get('date_end') or today
    
    # Comparison period
    period_days = (date_end - date_start).days + 1 if date_start and date_end else 30
    comp_date_start = date_start - timedelta(days=period_days) if date_start else None
    comp_date_end = date_start - timedelta(days=1) if date_start else None

    # Apply filters
    user_type = filters.get('user_type')
    min_sales = filters.get('min_sales')
    max_sales = filters.get('max_sales')
    query = filters.get('query')
    report_types = filters.get('report_type', ['sales', 'users', 'inventory', 'staff', 'customer'])

    data = {
        'summary': {},
        'detailed_reports': {},
        'summary_reports': {},
        'trend_reports': {},
        'exception_reports': {},
        'charts': {}
    }

    # Base querysets
    payment_qs = PaymentHistory.objects.select_related('user', 'delivery_info')
    user_qs = User.objects.all()
    review_qs = Review.objects.select_related('post__author')
    delivery_qs = DeliveryInfo.objects.all()
    
    if date_start:
        payment_qs = payment_qs.filter(created_at__date__gte=date_start)
        user_qs = user_qs.filter(date_joined__date__gte=date_start)
        review_qs = review_qs.filter(created_at__date__gte=date_start)
        delivery_qs = delivery_qs.filter(created_at__date__gte=date_start)
    
    if date_end:
        payment_qs = payment_qs.filter(created_at__date__lte=date_end)
        user_qs = user_qs.filter(date_joined__date__lte=date_end)
        review_qs = review_qs.filter(created_at__date__lte=date_end)
        delivery_qs = delivery_qs.filter(created_at__date__lte=date_end)
    
    # Comparison querysets
    comp_payment_qs = PaymentHistory.objects.all()
    comp_user_qs = User.objects.all()
    if comp_date_start:
        comp_payment_qs = comp_payment_qs.filter(created_at__date__gte=comp_date_start)
        comp_user_qs = comp_user_qs.filter(date_joined__date__gte=comp_date_start)
    if comp_date_end:
        comp_payment_qs = comp_payment_qs.filter(created_at__date__lte=comp_date_end)
        comp_user_qs = comp_user_qs.filter(date_joined__date__lte=comp_date_end)
    
    # Apply additional filters
    if user_type:
        payment_qs = payment_qs.filter(user__user_type=user_type)
        user_qs = user_qs.filter(user_type=user_type)
        comp_payment_qs = comp_payment_qs.filter(user__user_type=user_type)
        comp_user_qs = comp_user_qs.filter(user_type=user_type)
    
    if min_sales:
        payment_qs = payment_qs.filter(total__gte=min_sales)
        comp_payment_qs = comp_payment_qs.filter(total__gte=min_sales)
    
    if max_sales:
        payment_qs = payment_qs.filter(total__lte=max_sales)
        comp_payment_qs = comp_payment_qs.filter(total__lte=max_sales)
    
    if query:
        payment_qs = payment_qs.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
        user_qs = user_qs.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        review_qs = review_qs.filter(
            Q(post__title__icontains=query) |
            Q(post__content__icontains=query)
        )

    # Summary metrics
    total_revenue = payment_qs.aggregate(Sum('total'))['total__sum'] or 0
    total_orders = payment_qs.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    new_customers = user_qs.filter(user_type='customer').count()
    avg_rating = review_qs.aggregate(Avg('rating'))['rating__avg'] or 0
    
    comp_total_revenue = comp_payment_qs.aggregate(Sum('total'))['total__sum'] or 0
    comp_total_orders = comp_payment_qs.count()
    comp_avg_order_value = comp_total_revenue / comp_total_orders if comp_total_orders > 0 else 0
    comp_new_customers = comp_user_qs.filter(user_type='customer').count()
    
    revenue_growth = ((total_revenue - comp_total_revenue) / comp_total_revenue * 100) if comp_total_revenue > 0 else 0
    orders_growth = ((total_orders - comp_total_orders) / comp_total_orders * 100) if comp_total_orders > 0 else 0
    aov_growth = ((avg_order_value - comp_avg_order_value) / comp_avg_order_value * 100) if comp_avg_order_value > 0 else 0
    customer_growth = ((new_customers - comp_new_customers) / comp_new_customers * 100) if comp_new_customers > 0 else 0

    data['summary'] = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'new_customers': new_customers,
        'avg_rating': avg_rating,
        'revenue_growth': round(revenue_growth, 1),
        'orders_growth': round(orders_growth, 1),
        'aov_growth': round(aov_growth, 1),
        'customer_growth': round(customer_growth, 1),
        'period_start': date_start,
        'period_end': date_end,
        'comparison_start': comp_date_start,
        'comparison_end': comp_date_end,
    }

    # Monthly Sales
    monthly_sales = payment_qs.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total'),
        transaction_count=Count('id'),
        avg_order_value=Avg('total')
    ).order_by('month')
    
    monthly_sales_list = []
    prev_sales = None
    for item in monthly_sales:
        current_sales = item['total_sales'] or 0
        growth = None
        if prev_sales is not None and prev_sales > 0:
            growth = ((current_sales - prev_sales) / prev_sales * 100)
        monthly_sales_list.append({
            'month': item['month'].strftime('%B %Y'),
            'total_sales': current_sales,
            'transaction_count': item['transaction_count'],
            'avg_order_value': item['avg_order_value'] or 0,
            'growth': round(growth, 1) if growth is not None else None
        })
        prev_sales = current_sales
    
    data['summary_reports']['monthly_sales'] = monthly_sales_list
    
    # Sales trend for charts
    if monthly_sales_list and 'sales' in report_types:
        data['charts']['sales_trend'] = {
            'labels': [item['month'] for item in monthly_sales_list],
            'values': [float(item['total_sales']) for item in monthly_sales_list]
        }

    # Staff Performance
    if 'staff' in report_types:
        staff_performance = StaffAssignment.objects.filter(
            delivery__created_at__date__gte=date_start,
            delivery__created_at__date__lte=date_end
        ).values('staff__username').annotate(
            total_deliveries=Count('id'),
            completed_deliveries=Count('id', filter=Q(delivery__delivery_status='completed'))
        )
        
        if query:
            staff_performance = staff_performance.filter(staff__username__icontains=query)
        
        data['summary_reports']['staff_performance'] = [
            {
                'username': item['staff__username'],
                'total_deliveries': item['total_deliveries'],
                'completed_deliveries': item['completed_deliveries'],
                'completion_rate': round((item['completed_deliveries'] / item['total_deliveries'] * 100), 2) if item['total_deliveries'] else 0
            } for item in staff_performance.order_by('-total_deliveries')[:10]
        ]

    # Customer Satisfaction
    if 'customer' in report_types:
        reviews = review_qs
        data['summary_reports']['customer_satisfaction'] = {
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'average_food_rating': reviews.aggregate(Avg('food_rating'))['food_rating__avg'] or 0,
            'average_service_rating': reviews.aggregate(Avg('service_rating'))['service_rating__avg'] or 0,
            'average_ambiance_rating': reviews.aggregate(Avg('ambiance_rating'))['ambiance_rating__avg'] or 0,
            'total_reviews': reviews.count(),
            'positive_reviews': reviews.filter(rating__gte=4).count(),
            'negative_reviews': reviews.filter(rating__lt=3).count(),
        }

    # Recent Reviews
    if 'customer' in report_types:
        data['detailed_reports']['recent_reviews'] = [
            {
                'user': f"{r.post.author.first_name} {r.post.author.last_name}".strip() or r.post.author.username,
                'rating': r.rating,
                'comment': r.post.content,
                'date': r.created_at.strftime('%Y-%m-%d')
            } for r in review_qs.order_by('-created_at')[:10]
        ]

    # Top Selling Products
    if 'sales' in report_types:
        cart_ids = payment_qs.values_list('cart_id', flat=True)
        product_sales = defaultdict(lambda: {'units_sold': 0, 'revenue': 0})
        
        for cart_id in cart_ids:
            try:
                cart = Cart.objects.get(id=cart_id)
                items = CartItem.objects.filter(cart=cart).select_related('fast_food', 'food', 'drink')
                
                for item in items:
                    if item.fast_food:
                        product = item.fast_food
                        product_name = product.name
                        product_category = 'FastFood'
                        product_price = product.price
                    elif item.food:
                        product = item.food
                        product_name = product.name
                        product_category = 'Food'
                        product_price = product.price
                    elif item.drink:
                        product = item.drink
                        product_name = product.name
                        product_category = 'Drink'
                        product_price = product.price
                    else:
                        continue
                    
                    key = f"{product_name}|{product_category}"
                    product_sales[key]['units_sold'] += item.quantity
                    product_sales[key]['revenue'] += item.quantity * product_price
                    product_sales[key]['name'] = product_name
                    product_sales[key]['category'] = product_category
            except Cart.DoesNotExist:
                continue
        
        total_revenue_for_products = sum(item['revenue'] for item in product_sales.values())
        top_products = [
            {
                'name': values['name'],
                'category': values['category'],
                'units_sold': values['units_sold'],
                'revenue': values['revenue'],
                'percentage': round((values['revenue'] / total_revenue_for_products * 100), 1) if total_revenue_for_products > 0 else 0
            } for key, values in product_sales.items()
        ]
        data['detailed_reports']['top_products'] = sorted(top_products, key=lambda x: x['revenue'], reverse=True)[:10]

    # High-value Orders
    if 'sales' in report_types:
        high_value_orders = payment_qs.filter(total__gt=100).select_related('user').order_by('-total')
        data['exception_reports']['high_value_orders'] = [
            {
                'transaction_id': ph.transaction_id,
                'user': ph.user.username,
                'total': ph.total,
                'created_at': ph.created_at
            } for ph in high_value_orders[:10]
        ]

    # Low Inventory
    if 'inventory' in report_types:
        low_inventory = []
        inventory_threshold = 10
        for model in [FastFood, Food, Drink]:
            items = model.objects.filter(quantity__lt=inventory_threshold)
            if query:
                items = items.filter(name__icontains=query)
            low_inventory.extend([
                {
                    'product_id': getattr(item, 'product_id', item.pk),
                    'name': item.name,
                    'category': model.__name__,
                    'quantity': item.quantity,
                    'price': item.price,
                    'restock_urgency': 'CRITICAL' if item.quantity < 3 else 'HIGH' if item.quantity < 5 else 'MEDIUM'
                } for item in items
            ])
        data['exception_reports']['low_inventory'] = sorted(low_inventory, key=lambda x: x['quantity'])[:15]

    # Recent Payments
    if 'sales' in report_types:
        recent_payments = payment_qs.select_related('user', 'delivery_info').order_by('-created_at')
        data['detailed_reports']['payments'] = [
            {
                'transaction_id': ph.transaction_id,
                'user': ph.user.username,
                'total': ph.total,
                'created_at': ph.created_at,
                'payment_method': ph.delivery_info.payment_method if ph.delivery_info else 'Unknown'
            } for ph in recent_payments[:10]
        ]

    # New Customers
    if 'users' in report_types:
        new_customers = user_qs.filter(user_type='customer').order_by('-date_joined')
        data['detailed_reports']['customers'] = [
            {
                'full_name': f"{c.first_name} {c.last_name}".strip() or c.username,
                'email': c.email,
                'phone_number': c.phone_number or 'N/A',
                'date_joined': c.date_joined,
                'order_count': payment_qs.filter(user=c).count(),
                'total_spent': payment_qs.filter(user=c).aggregate(Sum('total'))['total__sum'] or 0
            } for c in new_customers[:10]
        ]

    # Sales Trend
    if 'sales' in report_types:
        sales_trend = []
        for i in range(1, len(monthly_sales_list)):
            current = monthly_sales_list[i]
            previous = monthly_sales_list[i-1]
            growth = ((current['total_sales'] - previous['total_sales']) / previous['total_sales'] * 100) if previous['total_sales'] > 0 else 0
            sales_trend.append({
                'month': current['month'],
                'total_sales': current['total_sales'],
                'growth': round(growth, 1)
            })
        data['trend_reports']['sales_trend'] = sales_trend

    # Customer Acquisition Trend
    if 'users' in report_types:
        customer_trend = user_qs.filter(user_type='customer').annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            new_customers=Count('id')
        ).order_by('month')
        data['trend_reports']['customer_trend'] = [
            {
                'month': item['month'].strftime('%B %Y'),
                'new_customers': item['new_customers']
            } for item in customer_trend
        ]

    return data

@login_required
def reports(request):
    if not request.user.is_superuser:
        return render(request, 'superadmin/permission_denied.html', status=403)
    
    form = AnalyticsFilterForm(request.GET or {
        'date_range': 'this_month',
        'report_type': ['sales', 'users', 'inventory', 'staff', 'customer']
    })
    
    context = {'form': form}
    if form.is_valid():
        context.update(get_enhanced_report_data(form.cleaned_data))
    else:
        context.update(get_enhanced_report_data())
    
    # Pagination for payments
    payments = context['detailed_reports'].get('payments', [])
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    context['detailed_reports']['payments_page'] = paginator.get_page(page_number)
    
    # Chart data
    if context['charts'].get('sales_trend'):
        context['charts']['sales_trend_json'] = json.dumps(context['charts']['sales_trend'])
    
    return render(request, 'superadmin/reports/reports.html', context)

@login_required
def reports_data(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    form = AnalyticsFilterForm(request.GET)
    if form.is_valid():
        data = get_enhanced_report_data(form.cleaned_data)
    else:
        data = get_enhanced_report_data()
    
    return JsonResponse({
        'sales_trend': data.get('charts', {}).get('sales_trend', {}),
        'summary': data.get('summary', {})
    })

