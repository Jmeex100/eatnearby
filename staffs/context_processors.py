from django.db.models import Q
from .models import Notification, DeliveryInfo
import logging

logger = logging.getLogger(__name__)

def staff_notifications(request):
    if not request.user.is_authenticated:
        logger.debug("User not authenticated, returning zero notification counts")
        return {
            'nav_dashboard_notifications': 0,
            'nav_deliveries_pending': 0,
            'nav_history_notifications': 0,
            'nav_availability_notifications': 0,
            'nav_total_notifications': 0,
        }

    # Dashboard: General unread notifications (e.g., system alerts, new assignments)
    dashboard_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        notification_type__in=['general', 'delivery_assignment']
    ).count()
    logger.debug(f"Dashboard notifications for user {request.user.id}: {dashboard_notifications}")

    # My Deliveries: Pending deliveries with payment confirmed or cash
    deliveries_pending = DeliveryInfo.objects.filter(
        staff_assignments__staff=request.user,
        delivery_status='pending'
    ).filter(
        Q(payment_histories__isnull=False) | Q(payment_method='cash')
    ).count()
    logger.debug(f"Pending deliveries for user {request.user.id}: {deliveries_pending}")

    # Delivery History: Unread notifications for completed or declined deliveries
    history_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    logger.debug(f"History notifications for user {request.user.id}: {history_notifications}")

    # Availability: Unread notifications for availability or schedule changes
    availability_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        notification_type='availability_update'
    ).count()
    logger.debug(f"Availability notifications for user {request.user.id}: {availability_notifications}")

    total_notifications = (
        dashboard_notifications +
        deliveries_pending +
        history_notifications +
        availability_notifications
    )
    logger.debug(f"Total notifications for user {request.user.id}: {total_notifications}")

    return {
        'nav_dashboard_notifications': dashboard_notifications,
        'nav_deliveries_pending': deliveries_pending,
        'nav_history_notifications': history_notifications,
        'nav_availability_notifications': availability_notifications,
        'nav_total_notifications': total_notifications,
    }