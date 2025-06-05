from django.shortcuts import render,redirect, get_object_or_404
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
    # Get current date and start of month
    today = timezone.now().date()
    month_start = today.replace(day=1)
    days_in_month = (today - month_start).days + 1

    # Filter completed payments
    completed_payments = PaymentHistory.objects.filter(
        delivery_info__delivery_status='completed'
    )

    # Today's revenue
    today_revenue = completed_payments.filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or 0

    # Monthly revenue
    monthly_revenue = completed_payments.filter(
        created_at__date__gte=month_start
    ).aggregate(total=Sum('total'))['total'] or 0

    # Daily average
    daily_average = round(monthly_revenue / days_in_month, 2) if days_in_month > 0 else 0

    # Payment methods breakdown
    payment_methods = []
    for method, method_display in DeliveryInfo.PAYMENT_METHODS:
        today_method_total = completed_payments.filter(
            delivery_info__payment_method=method,
            created_at__date=today
        ).aggregate(total=Sum('total'))['total'] or 0
        
        month_method_total = completed_payments.filter(
            delivery_info__payment_method=method,
            created_at__date__gte=month_start
        ).aggregate(total=Sum('total'))['total'] or 0
        
        percentage = round((month_method_total / monthly_revenue * 100), 2) if monthly_revenue > 0 else 0
        
        payment_methods.append({
            'name': method,
            'display_name': method_display,
            'today': today_method_total,
            'month': month_method_total,
            'percentage': percentage
        })

    # Recent transactions
    recent_transactions = completed_payments.select_related(
        'user', 'delivery_info'
    ).order_by('-created_at')[:5]

    context = {
        'revenue': {
            'today': today_revenue,
            'month': monthly_revenue,
            'daily_average': daily_average
        },
        'payment_methods': payment_methods,
        'recent_transactions': recent_transactions
    }
    return render(request, 'superadmin/revenue/revenue_dashboard.html', context)

@superadmin_required
def revenue_detail(request, method):
    # Validate payment method
    valid_methods = [m[0] for m in DeliveryInfo.PAYMENT_METHODS]
    if method not in valid_methods:
        messages.error(request, f"Invalid payment method: {method}")
        return redirect('superadmin:revenue_dashboard')

    # Get payments for the method
    payments = PaymentHistory.objects.filter(
        delivery_info__payment_method=method,
        delivery_info__delivery_status='completed'
    ).order_by('-created_at')

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
    method_display = dict(DeliveryInfo.PAYMENT_METHODS).get(method, method.title())

    context = {
        'page_obj': page_obj,
        'method': method_display,
        'product_type': 'Food',  # For consistency
    }
    return render(request, 'superadmin/revenue/revenue_detail.html', context)