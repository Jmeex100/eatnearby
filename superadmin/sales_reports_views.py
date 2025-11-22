from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.utils.timezone import now, localtime
from django.http import JsonResponse
from django.conf import settings
from django import forms
from auths.models import User, FastFood, Food, Drink, Category
from payments.models import PaymentHistory, DeliveryInfo
from cart.models import Cart, CartItem
from staffs.models import StaffAssignment, StaffServiceArea, Notification
from community.models import Review, Post, Restaurant, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer, Comment
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

# superadmin/sales_reports_views.py
# Enhanced Filter Form for Sales Reports
class SalesAnalyticsFilterForm(forms.Form):
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
    product_performance = forms.ChoiceField(
        choices=[('', 'All Products'), ('top_selling', 'Top Selling Products'), ('low_selling', 'Lowest Selling Products')],
        required=False, label="Product Performance"
    )

@login_required
def generate_sales_pdf_report(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=30, textColor=colors.HexColor('#1f2937'), alignment=1)  # Center aligned
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=12, textColor=colors.HexColor('#374151'), alignment=0)  # Left aligned
    subheading_style = ParagraphStyle('CustomSubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6, textColor=colors.HexColor('#4b5563'))
    normal_style = styles['BodyText']
    small_style = ParagraphStyle('SmallText', parent=styles['BodyText'], fontSize=8, alignment=1)  # Center aligned for footer

    # Header with logo
    logo_path = os.path.join(getattr(settings, 'STATIC_ROOT', ''), 'img', 'logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.5*inch, height=0.75*inch))

    elements.append(Paragraph("EATNEAR-BY SALES ANALYTICS REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {localtime(now()).strftime('%Y-%m-%d %H:%M')}", normal_style))

    # Display applied filters
    form = SalesAnalyticsFilterForm(request.GET)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        date_range = form.cleaned_data.get('date_range')
        user_type = form.cleaned_data.get('user_type')
        min_sales = form.cleaned_data.get('min_sales')
        max_sales = form.cleaned_data.get('max_sales')
        query = form.cleaned_data.get('query')
        report_types = form.cleaned_data.get('report_type', [])

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

        if 'product_performance' in request.GET and request.GET['product_performance']:
            product_perf = request.GET['product_performance']
            if product_perf == 'top_selling':
                filters.append("Product Performance: Top Selling Products")
            elif product_perf == 'low_selling':
                filters.append("Product Performance: Lowest Selling Products")

        if filters:
            # Create a formatted filter display
            elements.append(Paragraph("FILTERS APPLIED", subheading_style))
            for filter_item in filters:
                elements.append(Paragraph(f"• {filter_item}", normal_style))
            elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph("FILTERS APPLIED: None", subheading_style))
            elements.append(Spacer(1, 0.1 * inch))

    elements.append(Spacer(1, 0.25 * inch))

    # Always show all data in PDF regardless of applied filters - show complete Sales Analytics
    report_data = get_sales_report_data({
        'report_type': ['sales', 'products', 'payments']
    })

    # Sales Summary
    elements.append(Paragraph("SALES SUMMARY", heading_style))
    summary = report_data['summary']
    summary_data = [
        ["Metric", "Value", "Comparison", "Trend"],
        ["Total Revenue", f"K{summary['total_revenue']:,.2f}", f"{summary['revenue_growth']}% vs previous", "📈" if summary['revenue_growth'] > 0 else "📉"],
        ["Total Orders", f"{summary['total_orders']:,}", f"{summary['orders_growth']}% vs previous", "📈" if summary['orders_growth'] > 0 else "📉"],
        ["Average Order Value", f"K{summary['avg_order_value']:,.2f}", f"{summary['aov_growth']}% vs previous", "📈" if summary['aov_growth'] > 0 else "📉"],
        ["Total Products Sold", f"{summary['total_products_sold']:,}", "Units", "📦"],
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch, 0.8*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
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
        # Check if it's low selling or top selling based on filters
        product_perf_title = "TOP SELLING PRODUCTS"
        if hasattr(request, 'GET') and 'product_performance' in request.GET:
            if request.GET['product_performance'] == 'low_selling':
                product_perf_title = "LOWEST SELLING PRODUCTS"
        elements.append(Paragraph(product_perf_title, heading_style))
        top_products_data = [["Product", "Category", "Units Sold", "Revenue", "% of Total"]]
        for product in report_data['detailed_reports']['top_products']:
            top_products_data.append([
                product['name'][:30] + '...' if len(product['name']) > 30 else product['name'],
                product['category'],
                f"{product['units_sold']:,}",
                f"K{product['revenue']:,.2f}",
                f"{product['percentage']:.1f}%"
            ])

        top_products_table = Table(top_products_data, colWidths=[2*inch, 1.2*inch, 0.9*inch, 1.2*inch, 0.8*inch])
        top_products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(top_products_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Monthly Sales
    elements.append(Paragraph("MONTHLY SALES PERFORMANCE", heading_style))
    monthly_sales_data = [["Month", "Total Sales", "Transactions", "Avg. Order Value", "Growth"]]
    for item in report_data['summary_reports']['monthly_sales']:
        growth = item.get('growth')
        growth_symbol = "▲" if growth and growth > 0 else "▼" if growth and growth < 0 else "➖"
        monthly_sales_data.append([
            item['month'],
            f"K{item['total_sales']:,.2f}",
            f"{item['transaction_count']:,}",
            f"K{item.get('avg_order_value', 0):,.2f}",
            f"{growth_symbol} {abs(growth):.1f}%" if growth is not None else "N/A"
        ])

    monthly_sales_table = Table(monthly_sales_data, colWidths=[1.5*inch, 1.2*inch, 1*inch, 1.3*inch, 1*inch])
    monthly_sales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(monthly_sales_table)
    elements.append(Spacer(1, 0.25 * inch))

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

        high_value_table = Table(high_value_data, colWidths=[2*inch, 1.8*inch, 1.2*inch, 1.2*inch])
        high_value_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(high_value_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Recent Payments
    if report_data['detailed_reports'].get('payments'):
        elements.append(Paragraph("RECENT PAYMENTS", heading_style))
        recent_payments_data = [["Transaction ID", "User", "Total", "Date", "Payment Method"]]
        for payment in report_data['detailed_reports']['payments']:
            recent_payments_data.append([
                payment['transaction_id'],
                payment['user'],
                f"K{payment['total']:,.2f}",
                payment['created_at'].strftime('%Y-%m-%d'),
                payment['payment_method']
            ])

        recent_payments_table = Table(recent_payments_data, colWidths=[2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        recent_payments_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(recent_payments_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Sales Trend
    if report_data['trend_reports'].get('sales_trend'):
        elements.append(Paragraph("SALES TREND", heading_style))
        sales_trend_data = [["Month", "Total Sales", "Growth (%)"]]
        for item in report_data['trend_reports']['sales_trend']:
            growth_symbol = "▲" if item['growth'] > 0 else "▼" if item['growth'] < 0 else "➖"
            sales_trend_data.append([
                item['month'],
                f"K{item['total_sales']:,.2f}",
                f"{growth_symbol} {abs(item['growth']):.1f}%"
            ])

        sales_trend_table = Table(sales_trend_data, colWidths=[2.5*inch, 1.8*inch, 1.8*inch])
        sales_trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eab308')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eff6ff'), colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(sales_trend_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Footer
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Confidential - For Internal Use Only", small_style))
    elements.append(Paragraph(f"Report generated by {request.user.get_full_name() or request.user.username}", small_style))

    doc.build(elements)
    response = HttpResponse(content_type='application/pdf')
    filename = f"sales_analytics_report_{now().strftime('%Y%m%d_%H%M')}.pdf"
    disposition = 'attachment' if request.GET.get('download', '').lower() == 'true' else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    buffer.seek(0)
    response.write(buffer.read())
    buffer.close()
    return response

def get_sales_report_data(filters=None):
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
    report_types = filters.get('report_type', ['sales', 'products', 'payments'])
    product_performance = filters.get('product_performance')

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

    if date_start:
        payment_qs = payment_qs.filter(created_at__date__gte=date_start)
    if date_end:
        payment_qs = payment_qs.filter(created_at__date__lte=date_end)

    # Comparison querysets
    comp_payment_qs = PaymentHistory.objects.all()
    if comp_date_start:
        comp_payment_qs = comp_payment_qs.filter(created_at__date__gte=comp_date_start)
    if comp_date_end:
        comp_payment_qs = comp_payment_qs.filter(created_at__date__lte=comp_date_end)

    # Apply additional filters
    if user_type:
        payment_qs = payment_qs.filter(user__user_type=user_type)
        comp_payment_qs = comp_payment_qs.filter(user__user_type=user_type)

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

    # Summary metrics
    total_revenue = payment_qs.aggregate(Sum('total'))['total__sum'] or 0
    total_orders = payment_qs.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Calculate total products sold
    cart_ids = payment_qs.values_list('cart_id', flat=True)
    total_products_sold = 0
    for cart_id in cart_ids:
        try:
            cart = Cart.objects.get(id=cart_id)
            items = CartItem.objects.filter(cart=cart)
            total_products_sold += sum(item.quantity for item in items)
        except Cart.DoesNotExist:
            continue

    comp_total_revenue = comp_payment_qs.aggregate(Sum('total'))['total__sum'] or 0
    comp_total_orders = comp_payment_qs.count()
    comp_avg_order_value = comp_total_revenue / comp_total_orders if comp_total_orders > 0 else 0

    revenue_growth = ((float(total_revenue) - float(comp_total_revenue)) / float(comp_total_revenue) * 100) if comp_total_revenue > 0 else 0
    orders_growth = ((total_orders - comp_total_orders) / comp_total_orders * 100) if comp_total_orders > 0 else 0
    aov_growth = ((float(avg_order_value) - float(comp_avg_order_value)) / float(comp_avg_order_value) * 100) if comp_avg_order_value > 0 else 0

    data['summary'] = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'total_products_sold': total_products_sold,
        'revenue_growth': round(revenue_growth, 1),
        'orders_growth': round(orders_growth, 1),
        'aov_growth': round(aov_growth, 1),
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

    # Top Selling Products and Lowest Selling Products
    if 'products' in report_types:
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
        all_products = [
            {
                'name': values['name'],
                'category': values['category'],
                'units_sold': values['units_sold'],
                'revenue': values['revenue'],
                'percentage': round((values['revenue'] / total_revenue_for_products * 100), 1) if total_revenue_for_products > 0 else 0
            } for key, values in product_sales.items()
        ]

        # Filter based on product_performance
        if product_performance == 'top_selling':
            data['detailed_reports']['top_products'] = sorted(all_products, key=lambda x: x['revenue'], reverse=True)[:10]
        elif product_performance == 'low_selling':
            data['detailed_reports']['top_products'] = sorted(all_products, key=lambda x: x['revenue'])[:10]
        else:
            data['detailed_reports']['top_products'] = sorted(all_products, key=lambda x: x['revenue'], reverse=True)[:10]

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

    # Recent Payments
    if 'payments' in report_types:
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

    return data

@login_required
def sales_reports(request):
    if not request.user.is_superuser:
        return render(request, 'superadmin/permission_denied.html', status=403)

    form = SalesAnalyticsFilterForm(request.GET or {
        'date_range': 'this_year',
        'report_type': ['sales', 'users', 'inventory', 'staff', 'customer'],
        'product_performance': 'top_selling'
    })

    context = {'form': form}
    if form.is_valid():
        context.update(get_sales_report_data(form.cleaned_data))
    else:
        context.update(get_sales_report_data())

    # Pagination for payments
    payments = context['detailed_reports'].get('payments', [])
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    context['detailed_reports']['payments_page'] = paginator.get_page(page_number)

    # Chart data
    if context['charts'].get('sales_trend'):
        context['charts']['sales_trend_json'] = json.dumps(context['charts']['sales_trend'])

    return render(request, 'superadmin/reports/sales_reports.html', context)

@login_required
def sales_reports_data(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    form = SalesAnalyticsFilterForm(request.GET)
    if form.is_valid():
        data = get_sales_report_data(form.cleaned_data)
    else:
        data = get_sales_report_data()

    return JsonResponse({
        'sales_trend': data.get('charts', {}).get('sales_trend', {}),
        'summary': data.get('summary', {})
    })