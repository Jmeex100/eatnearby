from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from payments.models import PaymentHistory, DeliveryInfo
from .decorators import superadmin_required
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@superadmin_required
def revenue_dashboard(request):
    # Get date range from query parameters
    date_range = request.GET.get('range', 'month')
    today = timezone.now().date()
    start_date = None
    end_date = today

    # Set date range boundaries
    if date_range == 'today':
        start_date = today
        range_label = "Today"
    elif date_range == 'week':
        start_date = today - timedelta(days=6)
        range_label = "This Week"
    elif date_range == 'year':
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
    else:  # Default to month
        start_date = today.replace(day=1)
        range_label = "This Month"

    days_in_range = (end_date - start_date).days + 1 if start_date else (today - today.replace(day=1)).days + 1

    # Filter completed payments within date range
    completed_payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # Today's revenue
    today_revenue = completed_payments.filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or 0

    # Total revenue for the selected range
    total_revenue = completed_payments.aggregate(total=Sum('total'))['total'] or 0

    # Daily average
    daily_average = round(total_revenue / days_in_range, 2) if days_in_range > 0 else 0

    # Payment methods breakdown
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

    # Recent transactions
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
def revenue_detail(request, method):
    # Validate payment method
    valid_methods = [m[0] for m in DeliveryInfo.PAYMENT_METHODS]
    if method not in valid_methods and method != 'all':
        messages.error(request, f"Invalid payment method: {method}")
        return redirect('superadmin:revenue_dashboard')

    # Get date range from query parameters
    date_range = request.GET.get('range', 'month')
    today = timezone.now().date()
    start_date = None
    end_date = today

    # Set date range boundaries
    if date_range == 'today':
        start_date = today
        range_label = "Today"
    elif date_range == 'week':
        start_date = today - timedelta(days=6)
        range_label = "This Week"
    elif date_range == 'year':
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
    else:  # Default to month
        start_date = today.replace(day=1)
        range_label = "This Month"

    # Get payments for the method within date range
    payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    if method != 'all':
        payments = payments.filter(delivery_info__payment_method=method)
    
    payments = payments.order_by('-created_at')

    # Search functionality
    query = request.GET.get('q')
    if query:
        payments = payments.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    # Pagination
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get method display name
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