
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from auths.models import User, FastFood, Food, Drink
from payments.models import PaymentHistory, DeliveryInfo
from cart.models import Cart
from staffs.models import StaffAssignment
from community.models import Review
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
from django import forms
from datetime import timedelta

# Filter Form for Analytics Dashboard
class AnalyticsFilterForm(forms.Form):
    date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="End Date"
    )
    user_type = forms.ChoiceField(
        choices=[('', 'All'), ('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')],
        required=False,
        label="User Type"
    )
    min_sales = forms.DecimalField(
        required=False,
        min_value=0,
        label="Minimum Sales Amount"
    )
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={'placeholder': 'Search by transaction ID or username'})
    )

@login_required
def generate_pdf_report(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['BodyText']

    elements.append(Paragraph("Analytics Dashboard Report", title_style))
    elements.append(Paragraph(f"Generated on: {now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    
    # Display applied filters
    form = AnalyticsFilterForm(request.GET)
    if form.is_valid():
        date_start = form.cleaned_data.get('date_start')
        date_end = form.cleaned_data.get('date_end')
        user_type = form.cleaned_data.get('user_type')
        min_sales = form.cleaned_data.get('min_sales')
        query = form.cleaned_data.get('query')
        filter_text = "Filters Applied: "
        filters = []
        if date_start:
            filters.append(f"Start Date: {date_start}")
        if date_end:
            filters.append(f"End Date: {date_end}")
        if user_type:
            filters.append(f"User Type: {user_type.capitalize()}")
        if min_sales:
            filters.append(f"Min Sales: K{min_sales}")
        if query:
            filters.append(f"Search: {query}")
        filter_text += ", ".join(filters) if filters else "None"
        elements.append(Paragraph(filter_text, normal_style))
    
    elements.append(Spacer(1, 0.25 * inch))

    report_data = get_report_data(form.cleaned_data if form.is_valid() else {})

    # --- Summary: Monthly Sales ---
    elements.append(Paragraph("Summary Reports", heading_style))
    monthly_sales_data = [["Month", "Total Sales", "Transactions"]]
    for item in report_data['summary_reports']['monthly_sales']:
        monthly_sales_data.append([item['month'], f"K{item['total_sales']:.2f}", item['transaction_count']])
    monthly_sales_table = Table(monthly_sales_data)
    monthly_sales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Monthly Sales", styles['Heading3']))
    elements.append(monthly_sales_table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Staff Performance ---
    staff_performance_data = [["Staff", "Total Deliveries", "Completed", "Completion Rate"]]
    for item in report_data['summary_reports']['staff_performance']:
        staff_performance_data.append([
            item['username'],
            item['total_deliveries'],
            item['completed_deliveries'],
            f"{item['completion_rate']}%"
        ])
    staff_table = Table(staff_performance_data)
    staff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Staff Performance", styles['Heading3']))
    elements.append(staff_table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Customer Satisfaction ---
    customer_satisfaction = report_data['summary_reports'].get('customer_satisfaction', {})
    customer_satisfaction_data = [
        ["Metric", "Rating"],
        ["Overall Rating", f"{customer_satisfaction.get('average_rating', 0):.1f}"],
        ["Food Rating", f"{customer_satisfaction.get('average_food_rating', 0):.1f}"],
        ["Service Rating", f"{customer_satisfaction.get('average_service_rating', 0):.1f}"],
        ["Ambiance Rating", f"{customer_satisfaction.get('average_ambiance_rating', 0):.1f}"],
    ]
    customer_satisfaction_table = Table(customer_satisfaction_data)
    customer_satisfaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Customer Satisfaction", styles['Heading3']))
    elements.append(customer_satisfaction_table)
    elements.append(Spacer(1, 0.5 * inch))

    # --- Exception Reports ---
    elements.append(Paragraph("Exception Reports", heading_style))

    # High Value Orders
    high_value_data = [["Transaction ID", "Customer", "Amount", "Date"]]
    for item in report_data['exception_reports']['high_value_orders']:
        high_value_data.append([
            item['transaction_id'],
            item['user'],
            f"K{item['total']:.2f}",
            item['created_at'].strftime('%Y-%m-%d')
        ])
    high_value_table = Table(high_value_data)
    high_value_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("High Value Orders (>K100)", styles['Heading3']))
    elements.append(high_value_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Low Inventory Items
    low_inventory_data = [["Product ID", "Name", "Category", "Quantity"]]
    for item in report_data['exception_reports']['low_inventory']:
        low_inventory_data.append([
            item['product_id'],
            item['name'],
            item['category'],
            item['quantity']
        ])
    low_inventory_table = Table(low_inventory_data)
    low_inventory_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Low Inventory Items (<10)", styles['Heading3']))
    elements.append(low_inventory_table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Detailed Reports ---
    elements.append(Paragraph("Detailed Reports", heading_style))

    # Recent Payments
    recent_payments_data = [["Transaction ID", "User", "Total", "Date"]]
    for payment in report_data['detailed_reports']['payments']:
        recent_payments_data.append([
            payment['transaction_id'],
            payment['user'],
            f"K{payment['total']:.2f}",
            payment['created_at'].strftime('%Y-%m-%d')
        ])
    recent_payments_table = Table(recent_payments_data)
    recent_payments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Recent Payments", styles['Heading3']))
    elements.append(recent_payments_table)
    elements.append(Spacer(1, 0.25 * inch))

    # New Customers
    new_customers_data = [["Full Name", "Email", "Phone Number"]]
    for customer in report_data['detailed_reports']['customers']:
        new_customers_data.append([
            customer['full_name'],
            customer['email'],
            customer['phone_number']
        ])
    new_customers_table = Table(new_customers_data)
    new_customers_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(Paragraph("New Customers", styles['Heading3']))
    elements.append(new_customers_table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Trend Reports ---
    elements.append(Paragraph("Trend Reports", heading_style))

    # Sales Trend
    sales_trend_data = [["Month", "Total Sales", "Growth (%)"]]
    for item in report_data['trend_reports']['sales_trend']:
        sales_trend_data.append([
            item['month'],
            f"K{item['total_sales']:.2f}",
            f"{item['growth']}%"
        ])
    sales_trend_table = Table(sales_trend_data)
    sales_trend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Sales Trend", styles['Heading3']))
    elements.append(sales_trend_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Customer Acquisition Trend
    customer_trend_data = [["Month", "New Customers"]]
    for item in report_data['trend_reports']['customer_trend']:
        customer_trend_data.append([
            item['month'],
            item['new_customers']
        ])
    customer_trend_table = Table(customer_trend_data)
    customer_trend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(Paragraph("Customer Acquisition Trend", styles['Heading3']))
    elements.append(customer_trend_table)

    doc.build(elements)

    response = HttpResponse(content_type='application/pdf')
    filename = "analytics_report.pdf"
    if request.GET.get('download', '').lower() == 'true':
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    else:
        response['Content-Disposition'] = f'inline; filename="{filename}"'

    buffer.seek(0)
    response.write(buffer.read())
    buffer.close()
    return response

def get_report_data(filters=None):
    if filters is None:
        filters = {}
    data = {
        'detailed_reports': {},
        'summary_reports': {},
        'trend_reports': {},
        'exception_reports': {},
    }

    # Apply filters
    date_start = filters.get('date_start')
    date_end = filters.get('date_end')
    user_type = filters.get('user_type')
    min_sales = filters.get('min_sales')
    query = filters.get('query')

    # Monthly Sales
    monthly_sales = PaymentHistory.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total'),
        transaction_count=Count('id')
    )
    if date_start:
        monthly_sales = monthly_sales.filter(created_at__gte=date_start)
    if date_end:
        monthly_sales = monthly_sales.filter(created_at__lte=date_end + timedelta(days=1))
    if user_type:
        monthly_sales = monthly_sales.filter(user__user_type=user_type)
    if min_sales:
        monthly_sales = monthly_sales.filter(total_sales__gte=min_sales)
    if query:
        monthly_sales = monthly_sales.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    data['summary_reports']['monthly_sales'] = [
        {
            'month': item['month'].strftime('%B %Y'),
            'total_sales': item['total_sales'] or 0,
            'transaction_count': item['transaction_count'] or 0
        } for item in monthly_sales.order_by('-month')[:12]
    ]

    # Staff Performance
    staff_performance = StaffAssignment.objects.select_related('staff').values(
        'staff__username'
    ).annotate(
        total_deliveries=Count('id'),
        completed_deliveries=Count('id', filter=Q(delivery__delivery_status='completed'))
    )
    if date_start:
        staff_performance = staff_performance.filter(delivery__created_at__gte=date_start)
    if date_end:
        staff_performance = staff_performance.filter(delivery__created_at__lte=date_end + timedelta(days=1))
    if query:
        staff_performance = staff_performance.filter(staff__username__icontains=query)
    
    data['summary_reports']['staff_performance'] = [
        {
            'username': item['staff__username'],
            'total_deliveries': item['total_deliveries'],
            'completed_deliveries': item['completed_deliveries'],
            'completion_rate': round((item['completed_deliveries'] / item['total_deliveries'] * 100), 2)
            if item['total_deliveries'] else 0
        } for item in staff_performance.order_by('-total_deliveries')[:10]
    ]

    # Customer Satisfaction
    reviews = Review.objects.all()
    if date_start:
        reviews = reviews.filter(created_at__gte=date_start)
    if date_end:
        reviews = reviews.filter(created_at__lte=date_end + timedelta(days=1))
    if query:
        reviews = reviews.filter(user__username__icontains=query)
    
    data['summary_reports']['customer_satisfaction'] = {
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'average_food_rating': reviews.aggregate(Avg('food_rating'))['food_rating__avg'] or 0,
        'average_service_rating': reviews.aggregate(Avg('service_rating'))['service_rating__avg'] or 0,
        'average_ambiance_rating': reviews.aggregate(Avg('ambiance_rating'))['ambiance_rating__avg'] or 0,
    }

    # High-value Orders
    high_value_orders = PaymentHistory.objects.filter(total__gt=100).select_related('user')
    if date_start:
        high_value_orders = high_value_orders.filter(created_at__gte=date_start)
    if date_end:
        high_value_orders = high_value_orders.filter(created_at__lte=date_end + timedelta(days=1))
    if user_type:
        high_value_orders = high_value_orders.filter(user__user_type=user_type)
    if query:
        high_value_orders = high_value_orders.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    data['exception_reports']['high_value_orders'] = [
        {
            'transaction_id': ph.transaction_id,
            'user': ph.user.username,
            'total': ph.total,
            'created_at': ph.created_at
        } for ph in high_value_orders[:10]
    ]

    # Low Inventory Items
    low_inventory = []
    for model in [FastFood, Food, Drink]:
        items = model.objects.filter(quantity__lt=10)
        if query:
            items = items.filter(name__icontains=query)
        low_inventory.extend([
            {
                'product_id': getattr(item, 'product_id', item.pk),  # Use product_id if available, else fallback to pk
                'name': item.name,
                'category': model.__name__,
                'quantity': item.quantity
            } for item in items
        ])
    data['exception_reports']['low_inventory'] = low_inventory[:10]

    # Recent Payments
    recent_payments = PaymentHistory.objects.select_related('user').order_by('-created_at')
    if date_start:
        recent_payments = recent_payments.filter(created_at__gte=date_start)
    if date_end:
        recent_payments = recent_payments.filter(created_at__lte=date_end + timedelta(days=1))
    if user_type:
        recent_payments = recent_payments.filter(user__user_type=user_type)
    if query:
        recent_payments = recent_payments.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    data['detailed_reports']['payments'] = [
        {
            'transaction_id': ph.transaction_id,
            'user': ph.user.username,
            'total': ph.total,
            'created_at': ph.created_at
        } for ph in recent_payments[:10]
    ]

    # New Customers
    new_customers = User.objects.filter(user_type='customer').order_by('-date_joined')
    if date_start:
        new_customers = new_customers.filter(date_joined__gte=date_start)
    if date_end:
        new_customers = new_customers.filter(date_joined__lte=date_end + timedelta(days=1))
    if query:
        new_customers = new_customers.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    data['detailed_reports']['customers'] = [
        {
            'full_name': f"{c.first_name} {c.last_name}".strip(),
            'email': c.email,
            'phone_number': c.phone_number or 'N/A'
        } for c in new_customers[:10]
    ]

    # Sales Trend
    monthly_sales = PaymentHistory.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total')
    )
    if date_start:
        monthly_sales = monthly_sales.filter(created_at__gte=date_start)
    if date_end:
        monthly_sales = monthly_sales.filter(created_at__lte=date_end + timedelta(days=1))
    if user_type:
        monthly_sales = monthly_sales.filter(user__user_type=user_type)
    if query:
        monthly_sales = monthly_sales.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    sales_trend = []
    monthly_sales = monthly_sales.order_by('month')[:12]
    for i, item in enumerate(monthly_sales):
        if i > 0:
            prev_sales = monthly_sales[i-1]['total_sales'] or 0
            current_sales = item['total_sales'] or 0
            growth = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales else 0
            sales_trend.append({
                'month': item['month'].strftime('%B %Y'),
                'total_sales': current_sales,
                'growth': round(growth, 2)
            })
    
    data['trend_reports']['sales_trend'] = sales_trend

    # Customer Acquisition Trend
    customer_trend = User.objects.filter(user_type='customer').annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        new_customers=Count('id')
    )
    if date_start:
        customer_trend = customer_trend.filter(date_joined__gte=date_start)
    if date_end:
        customer_trend = customer_trend.filter(date_joined__lte=date_end + timedelta(days=1))
    if query:
        customer_trend = customer_trend.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    data['trend_reports']['customer_trend'] = [
        {
            'month': item['month'].strftime('%B %Y'),
            'new_customers': item['new_customers']
        } for item in customer_trend.order_by('month')[:12]
    ]

    return data

@login_required
def reports(request):
    if not request.user.is_superuser:
        return render(request, 'superadmin/permission_denied.html', status=403)
    
    form = AnalyticsFilterForm(request.GET)
    context = {'form': form}
    if form.is_valid():
        context.update(get_report_data(form.cleaned_data))
    else:
        context.update(get_report_data())
    # Add pagination
    paginator = Paginator(context['detailed_reports']['payments'], 10)
    page_number = request.GET.get('page')
    context['detailed_reports']['payments'] = paginator.get_page(page_number)
    return render(request, 'superadmin/reports/reports.html', context)