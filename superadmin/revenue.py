# superadmin/revenue.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from payments.models import PaymentHistory, DeliveryInfo
from .decorators import superadmin_required
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@superadmin_required
def revenue_dashboard(request):
    date_range = request.GET.get('range', 'this_month')
    today = timezone.now().date()
    start_date = None
    end_date = today

    if date_range == 'today':
        start_date = today
        range_label = "Today"
    elif date_range == 'this_week':
        start_date = today - timedelta(days=6)
        range_label = "This Week"
    elif date_range == 'this_year':
        start_date = today.replace(month=1, day=1)
        range_label = "This Year"
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            range_label = f"Custom: {start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except (ValueError, TypeError):
            messages.error(request, "Invalid date range")
            return redirect('superadmin:revenue_dashboard')
    else:
        start_date = today.replace(day=1)
        range_label = "This Month"

    days_in_range = (end_date - start_date).days + 1 if start_date else (today - today.replace(day=1)).days + 1

    completed_payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    today_revenue = completed_payments.filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or 0

    total_revenue = completed_payments.aggregate(total=Sum('total'))['total'] or 0

    daily_average = round(total_revenue / days_in_range, 2) if days_in_range > 0 else 0

    payment_methods = []
    for method, method_display in DeliveryInfo.PAYMENT_METHODS:
        today_method_total = completed_payments.filter(
            delivery_info__payment_method=method,
            created_at__date=today
        ).aggregate(total=Sum('total'))['total'] or 0
        
        range_method_total = completed_payments.filter(
            delivery_info__payment_method=method
        ).aggregate(total=Sum('total'))['total'] or 0
        
        percentage = round((range_method_total / total_revenue * 100), 2) if total_revenue > 0 else 0
        
        payment_methods.append({
            'name': method,
            'display_name': method_display,
            'today': today_method_total,
            'total': range_method_total,
            'percentage': percentage
        })

    recent_transactions = completed_payments.select_related(
        'user', 'delivery_info'
    ).order_by('-created_at')[:5]

    context = {
        'revenue': {
            'today': today_revenue,
            'total': total_revenue,
            'daily_average': daily_average
        },
        'payment_methods': payment_methods,
        'recent_transactions': recent_transactions,
        'date_range': date_range,
        'range_label': range_label,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'superadmin/revenue/revenue_dashboard.html', context)

@superadmin_required
def generate_revenue_pdf(request):
    date_range = request.GET.get('range', 'this_month')
    today = timezone.now().date()
    start_date = None
    end_date = today

    if date_range == 'today':
        start_date = today
        range_label = "Today"
    elif date_range == 'this_week':
        start_date = today - timedelta(days=6)
        range_label = "This Week"
    elif date_range == 'this_year':
        start_date = today.replace(month=1, day=1)
        range_label = "This Year"
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            range_label = f"Custom: {start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except (ValueError, TypeError):
            messages.error(request, "Invalid date range")
            return redirect('superadmin:revenue_dashboard')
    else:
        start_date = today.replace(day=1)
        range_label = "This Month"

    completed_payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    today_revenue = completed_payments.filter(created_at__date=today).aggregate(total=Sum('total'))['total'] or 0
    total_revenue = completed_payments.aggregate(total=Sum('total'))['total'] or 0
    days_in_range = (end_date - start_date).days + 1 if start_date else (today - today.replace(day=1)).days + 1
    daily_average = round(total_revenue / days_in_range, 2) if days_in_range > 0 else 0

    payment_methods = []
    for method, method_display in DeliveryInfo.PAYMENT_METHODS:
        range_method_total = completed_payments.filter(delivery_info__payment_method=method).aggregate(total=Sum('total'))['total'] or 0
        percentage = round((range_method_total / total_revenue * 100), 2) if total_revenue > 0 else 0
        payment_methods.append({
            'name': method_display,
            'total': range_method_total,
            'percentage': percentage
        })

    recent_transactions = completed_payments.select_related('user', 'delivery_info').order_by('-created_at')[:5]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch, bottomMargin=inch/2)
    styles = getSampleStyleSheet()
    elements = []

    # Logo
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=2*inch, height=0.5*inch))
    elements.append(Spacer(1, 0.25*inch))

    # Title
    elements.append(Paragraph(f"Revenue Report: {range_label}", styles['Title']))
    elements.append(Spacer(1, 0.25*inch))

    # Summary
    elements.append(Paragraph("Summary", styles['Heading2']))
    summary_data = [
        ["Metric", "Value"],
        ["Total Revenue", f"K{total_revenue:.2f}"],
        ["Today's Revenue", f"K{today_revenue:.2f}"],
        ["Daily Average", f"K{daily_average:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25*inch))

    # Payment Methods
    elements.append(Paragraph("Payment Methods", styles['Heading2']))
    payment_data = [["Method", "Total", "Percentage"]]
    for method in payment_methods:
        payment_data.append([method['name'], f"K{method['total']:.2f}", f"{method['percentage']:.2f}%"])
    payment_table = Table(payment_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.25*inch))

    # Recent Transactions
    elements.append(Paragraph("Recent Transactions", styles['Heading2']))
    transaction_data = [["ID", "Date", "Customer", "Method", "Amount"]]
    for transaction in recent_transactions:
        transaction_data.append([
            transaction.transaction_id[:10],
            transaction.created_at.strftime('%b %d, %Y %H:%M'),
            transaction.user.get_full_name() or transaction.user.username,
            transaction.delivery_info.get_payment_method_display(),
            f"K{transaction.total:.2f}"
        ])
    transaction_table = Table(transaction_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch])
    transaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(transaction_table)

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="revenue_report_{range_label.replace(" ", "_")}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response

@superadmin_required
def revenue_detail(request, method):
    valid_methods = [m[0] for m in DeliveryInfo.PAYMENT_METHODS]
    if method not in valid_methods and method != 'all':
        messages.error(request, f"Invalid payment method: {method}")
        return redirect('superadmin:revenue_dashboard')

    date_range = request.GET.get('range', 'this_month')
    today = timezone.now().date()
    start_date = None
    end_date = today

    if date_range == 'today':
        start_date = today
        range_label = "Today"
    elif date_range == 'this_week':
        start_date = today - timedelta(days=6)
        range_label = "This Week"
    elif date_range == 'this_year':
        start_date = today.replace(month=1, day=1)
        range_label = "This Year"
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            range_label = f"Custom: {start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except (ValueError, TypeError):
            messages.error(request, "Invalid date range")
            return redirect('superadmin:revenue_dashboard')
    else:
        start_date = today.replace(day=1)
        range_label = "This Month"

    payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    if method != 'all':
        payments = payments.filter(delivery_info__payment_method=method)
    
    payments = payments.order_by('-created_at')

    query = request.GET.get('q')
    if query:
        payments = payments.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    method_display = dict(DeliveryInfo.PAYMENT_METHODS).get(method, method.title()) if method != 'all' else 'All Payment Methods'

    context = {
        'page_obj': page_obj,
        'method': method_display,
        'product_type': 'Food',
        'date_range': date_range,
        'range_label': range_label,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'superadmin/revenue/revenue_detail.html', context)