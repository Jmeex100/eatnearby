from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from auths.models import User
from .models import Notification
from payments.models import DeliveryInfo
# In your views.py staffs/delivery.py
def get_notification_count(user):
    """Helper function to get unread notification count for a user"""
    if user.is_authenticated:
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    return 0

def get_notifications(user, limit=5):
    """Helper function to get recent unread notifications"""
    if user.is_authenticated:
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).order_by('-created_at')[:limit]
    return Notification.objects.none()

@login_required
def assign_delivery(request):
    context = {
        'unread_notifications_count': get_notification_count(request.user),
        'notifications': get_notifications(request.user)
    }
    return render(request, 'staffs/assign_delivery.html', context)

@login_required
def order_reports(request):
    context = {
        'unread_notifications_count': get_notification_count(request.user),
        'notifications': get_notifications(request.user)
    }
    return render(request, 'staffs/order_reports.html', context)

@login_required
def delivery_zones(request):
    context = {
        'unread_notifications_count': get_notification_count(request.user),
        'notifications': get_notifications(request.user)
    }
    return render(request, 'staffs/delivery_zones.html', context)

@login_required
def active_deliveries(request):
    active_deliveries = DeliveryInfo.objects.filter(
        delivery_status='in_progress'
    ).order_by('-created_at')
    
    context = {
        'deliveries': active_deliveries,
        'unread_notifications_count': get_notification_count(request.user),
        'notifications': get_notifications(request.user)
    }
    return render(request, 'staffs/active_deliveries.html', context)