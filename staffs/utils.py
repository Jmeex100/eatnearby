from django.utils.timezone import now, timedelta
from  .import StaffAssignment, Notification

def get_badge_counts(staff):
    """Calculate badge counts for dashboard, history, and availability notifications."""
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    return {
        'dashboard_notifications': Notification.objects.filter(
            recipient=staff,
            is_read=False,
            notification_type='new_order'
        ).count(),
        'history_notifications': Notification.objects.filter(
            recipient=staff,
            is_read=False,
            notification_type__in=['delivery_completed', 'delivery_declined']
        ).count(),
        'availability_notifications': StaffAssignment.objects.filter(
            staff=staff,
            assigned_at__gte=today_start,
            assigned_at__lt=today_end
        ).count(),
    }