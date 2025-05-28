from django.shortcuts import render, redirect
from django.contrib import messages
from auths.models import User
from payments.models import DeliveryInfo, PaymentHistory
from django.db.models import Sum
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone
from .decorators import superadmin_required

@superadmin_required
def dashboard(request):
    user_counts = {
        'total': User.objects.count(),
        'admin': User.objects.filter(user_type='admin').count(),
        'staff': User.objects.filter(user_type='staff').count(),
        'customer': User.objects.filter(user_type='customer').count(),
    }

    delivery_counts = {
        'active': DeliveryInfo.objects.filter(delivery_status__in=['pending', 'in_progress']).count(),
        'completed': DeliveryInfo.objects.filter(delivery_status='completed').count(),
        'cancelled': DeliveryInfo.objects.filter(delivery_status='cancelled').count(),
    }

    today = timezone.now().date()
    month_start = today.replace(day=1)
    revenue = {
        'today': PaymentHistory.objects.filter(created_at__date=today).aggregate(Sum('total'))['total__sum'] or 0,
        'month': PaymentHistory.objects.filter(created_at__gte=month_start).aggregate(Sum('total'))['total__sum'] or 0,
    }

    recent_users = User.objects.all().order_by('-date_joined')[:5]

    recent_activities = []
    for user in recent_users:
        try:
            action_url = reverse('superadmin:user_detail', args=[user.id]) if user.id else None
            recent_activities.append({
                'title': 'New User Registered',
                'description': f'User {user.username} joined as {user.get_user_type_display()}',
                'timestamp': user.date_joined,
                'icon': 'user-plus',
                'color': 'blue',
                'action_url': action_url,
            })
        except Exception as e:
            print(f"Error generating action_url for user {user.username}: {e}")
            recent_activities.append({
                'title': 'New User Registered',
                'description': f'User {user.username} joined as {user.get_user_type_display()}',
                'timestamp': user.date_joined,
                'icon': 'user-plus',
                'color': 'blue',
                'action_url': None,
            })

    new_deliveries = DeliveryInfo.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))[:3]
    for delivery in new_deliveries:
        recent_activities.append({
            'title': 'New Delivery Created',
            'description': f'Delivery #{delivery.id} for {delivery.user.username}',
            'timestamp': delivery.created_at,
            'icon': 'truck',
            'color': 'green',
            'action_url': reverse('superadmin:delivery_detail', args=[delivery.id]) if delivery.id else None,
        })

    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:5]

    context = {
        'user_counts': user_counts,
        'delivery_counts': delivery_counts,
        'revenue': revenue,
        'recent_users': recent_users,
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

