from django.shortcuts import render, redirect
from django.contrib import messages
from auths.models import User
from payments.models import DeliveryInfo, PaymentHistory
from django.db.models import Sum
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone
from .decorators import superadmin_required
from django.shortcuts import render, redirect
from django.contrib import messages
from auths.models import User
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import Notification
from django.db.models import Sum, Count, Q
from django.urls import reverse
from datetime import datetime, timedelta
from staffs.models import StaffServiceArea, StaffAssignment
from django.utils import timezone
from django.core.cache import cache
from .decorators import superadmin_required
import json
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from auths.models import User, Category, FastFood, Food, Drink
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification
from .decorators import superadmin_required

@superadmin_required
def dashboard(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # User statistics
    user_counts = {
        'total': User.objects.count(),
        'admin': User.objects.filter(user_type='admin').count(),
        'staff': User.objects.filter(user_type='staff').count(),
        'customer': User.objects.filter(user_type='customer').count(),
    }

    # Delivery statistics
    delivery_counts = {
        'active': DeliveryInfo.objects.filter(delivery_status__in=['pending', 'in_progress']).count(),
        'completed': DeliveryInfo.objects.filter(delivery_status='completed').count(),
        'cancelled': DeliveryInfo.objects.filter(delivery_status='cancelled').count(),
    }

    # Revenue statistics
    revenue = {
        'today': PaymentHistory.objects.filter(created_at__date=today).aggregate(Sum('total'))['total__sum'] or 0,
        'week': PaymentHistory.objects.filter(created_at__gte=week_start).aggregate(Sum('total'))['total__sum'] or 0,
        'month': PaymentHistory.objects.filter(created_at__gte=month_start).aggregate(Sum('total'))['total__sum'] or 0,
    }

    # Category statistics
    category_counts = {
        'total': Category.objects.count(),
        'categories': Category.objects.annotate(
            product_count=Count('fastfood_products') + Count('food_products') + Count('drink_products')
        ).order_by('-product_count')[:5],  # Top 5 categories by product count
    }

    # Product statistics
    product_counts = {
        'fastfood': FastFood.objects.count(),
        'food': Food.objects.count(),
        'drink': Drink.objects.count(),
        'total': FastFood.objects.count() + Food.objects.count() + Drink.objects.count(),
    }

    # Staff service area statistics
    staff_service_areas = StaffServiceArea.objects.select_related('staff').values(
        'point'
    ).annotate(
        staff_count=Count('staff')
    ).order_by('-staff_count')[:5]  # Top 5 service areas by staff count

    # Staff assignment statistics
    assignment_counts = {
        'total': StaffAssignment.objects.count(),
        'recent': StaffAssignment.objects.select_related('staff', 'delivery').order_by('-assigned_at')[:3],
    }

    # Notification statistics
    notification_counts = {
        'total': Notification.objects.count(),
        'unread': Notification.objects.filter(is_read=False).count(),
        'recent': Notification.objects.filter(recipient__user_type='staff').order_by('-created_at')[:5],
    }

    # Payment history statistics
    payment_counts = {
        'total': PaymentHistory.objects.count(),
        'recent': PaymentHistory.objects.select_related('user', 'delivery_info').order_by('-created_at')[:5],
    }

    # Recent activities (extended to include product and category updates)
    recent_activities = []
    
    # User registrations
    recent_users = User.objects.all().order_by('-date_joined')[:3]
    for user in recent_users:
        recent_activities.append({
            'title': f'New {user.get_user_type_display()} registered',
            'message': f'{user.get_full_name()} joined the system',
            'timestamp': user.date_joined,
            'icon': 'user-plus',
            'color': 'blue',
            'is_read': True,
        })

    # Recent deliveries
    recent_deliveries = DeliveryInfo.objects.select_related('user').order_by('-created_at')[:3]
    for delivery in recent_deliveries:
        recent_activities.append({
            'title': 'New Delivery',
            'message': f'Order #{delivery.id} from {delivery.user.username}',
            'timestamp': delivery.created_at,
            'icon': 'truck',
            'color': 'green',
            'is_read': True,
        })

    # Recent payments
    recent_payments = PaymentHistory.objects.select_related('user').order_by('-created_at')[:2]
    for payment in recent_payments:
        recent_activities.append({
            'title': 'Payment Received',
            'message': f'K{payment.total} from {payment.user.username}',
            'timestamp': payment.created_at,
            'icon': 'money-bill-wave',
            'color': 'purple',
            'is_read': True,
        })

    # Recent products
    recent_products = (
        list(FastFood.objects.order_by('-created_at')[:2]) +
        list(Food.objects.order_by('-created_at')[:2]) +
        list(Drink.objects.order_by('-created_at')[:2])
    )
    for product in recent_products[:3]:  # Limit to 3 to avoid overcrowding
        recent_activities.append({
            'title': f'New {product.__class__.__name__} Added',
            'message': f'{product.name} (K{product.price}) in {product.category.name}',
            'timestamp': product.created_at,
            'icon': 'utensils',
            'color': 'yellow',
            'is_read': True,
        })

    # Sort activities by timestamp
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:5]

    context = {
        'today': today,
        'month_start': month_start,
        'user_counts': user_counts,
        'delivery_counts': delivery_counts,
        'revenue': revenue,
        'category_counts': category_counts,
        'product_counts': product_counts,
        'staff_service_areas': staff_service_areas,
        'assignment_counts': assignment_counts,
        'notification_counts': notification_counts,
        'payment_counts': payment_counts,
        'recent_users': recent_users,
        'recent_assignments': assignment_counts['recent'],
        'recent_notifications': notification_counts['recent'],
        'recent_activities': recent_activities,
    }
    return render(request, 'superadmin/dashboard.html', context)
@superadmin_required
def system_settings(request):
    if request.method == 'POST':
        # Handle settings form (e.g., site name)
        messages.success(request, "Settings updated successfully.")
        return redirect('superadmin:system_settings')
    return render(request, 'superadmin/settings/system_settings.html')

