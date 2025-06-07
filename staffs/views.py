from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.http import JsonResponse
import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import now, timedelta
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib import messages
from payments.models import DeliveryInfo, PaymentHistory
from .models import StaffAssignment, Notification
from .staffs_decorator import staff_view
from django.contrib.auth import get_user_model
from payments.mobile.twilio_utils import send_sms
from .staffs_decorator import staff_view
from django.contrib.auth import get_user_model
from payments.mobile.twilio_utils import send_sms
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import now, timedelta
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib import messages
from payments.models import DeliveryInfo, PaymentHistory
from .models import StaffAssignment, Notification
from .staffs_decorator import staff_view
from django.contrib.auth import get_user_model
from payments.mobile.twilio_utils import send_sms
import logging
import json
from typing import Dict, Optional
import json
from typing import Dict, Optional
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

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

@login_required
@staff_view
def dashboard(request):
    today = now().date()
    staff = request.user

    # Delivery stats
    stats = StaffAssignment.objects.filter(staff=staff).aggregate(
        active_count=Count('id', filter=Q(delivery__delivery_status='in_progress')),
        completed_today_count=Count('id', filter=Q(delivery__delivery_status='completed', delivery__updated_at__date=today)),
        total_completed_count=Count('id', filter=Q(delivery__delivery_status='completed')),
        pending_count=Count('id', filter=Q(delivery__delivery_status='pending'))
    )

    active_deliveries = stats['active_count']
    completed_today = stats['completed_today_count']
    total_completed = stats['total_completed_count']
    pending_count = stats['pending_count']
    on_time_rate = 0 if total_completed == 0 else round((completed_today / total_completed) * 100)

    # Payment history with optimized queries
    payment_history = PaymentHistory.objects.filter(
        delivery_info__staff_assignments__staff=staff
    ).select_related('delivery_info', 'user').prefetch_related('delivery_info__staff_assignments').order_by('-created_at')

    paginator = Paginator(payment_history, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Badge counts for sidebar_items.html
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    context = {
        'my_deliveries': {
            'active_count': active_deliveries,
            'completed_today': completed_today,
            'on_time_rate': on_time_rate,
            'pending_count': pending_count
        },
        'payment_history': page_obj,
        'page_obj': page_obj,
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
        'last_login': staff.last_login,
        'staff_name': staff.get_full_name() or staff.username,
    }
    return render(request, 'staffs/dashboard.html', context)
@login_required
@staff_view
def my_deliveries(request):
    today = now().date()
    staff = request.user

    stats = StaffAssignment.objects.filter(staff=staff).aggregate(
        active_count=Count('id', filter=Q(delivery__delivery_status='in_progress')),
        completed_today_count=Count('id', filter=Q(delivery__delivery_status='completed', delivery__updated_at__date=today)),
        total_completed_count=Count('id', filter=Q(delivery__delivery_status='completed')),
        pending_count=Count('id', filter=Q(delivery__delivery_status='pending'))
    )

    pending_deliveries = DeliveryInfo.objects.filter(
        staff_assignments__staff=staff,
        delivery_status='pending'
    ).filter(
        Q(payment_histories__isnull=False) | Q(payment_method='cash')
    ).select_related('user', 'cart').order_by('-created_at')

    in_progress_deliveries = DeliveryInfo.objects.filter(
        staff_assignments__staff=staff,
        delivery_status='in_progress'
    ).select_related('user', 'cart').order_by('-created_at')

    # Badge counts
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    context = {
        'my_deliveries': {
            'active_count': stats['active_count'],
            'completed_today': stats['completed_today_count'],
            'on_time_rate': 0 if stats['total_completed_count'] == 0 else round((stats['completed_today_count'] / stats['total_completed_count']) * 100),
            'pending_count': stats['pending_count']
        },
        'pending_deliveries': pending_deliveries,
        'in_progress_deliveries': in_progress_deliveries,
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
    }
    return render(request, 'staffs/my_deliveries.html', context)

@login_required
@staff_view
def delivery_history(request):
    staff = request.user
    deliveries = DeliveryInfo.objects.filter(
        staff_assignments__staff=staff
    ).select_related('user').order_by('-updated_at')

    notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False
    ).order_by('-created_at')[:10]
    logger.debug(f"Notifications for user {staff.id}: {[n.id for n in notifications]}")

    # Badge counts
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    context = {
        'deliveries': deliveries,
        'notifications': notifications,
        'my_deliveries': {
            'active_count': StaffAssignment.objects.filter(
                staff=staff,
                delivery__delivery_status='in_progress'
            ).count()
        },
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
    }
    return render(request, 'staffs/delivery_history.html', context)

@login_required
@require_POST
def accept_delivery(request, delivery_id):
    delivery = get_object_or_404(DeliveryInfo, id=delivery_id)
    if delivery.delivery_status != 'pending':
        messages.warning(request, "This delivery has already been accepted or processed.")
        return redirect('staffs:my_deliveries')
    assignment = StaffAssignment.objects.filter(staff=request.user, delivery=delivery).first()
    if not assignment:
        messages.error(request, "You are not assigned to this delivery.")
        return redirect('staffs:my_deliveries')
    if delivery.payment_method != 'cash' and not PaymentHistory.objects.filter(delivery_info=delivery).exists():
        messages.error(request, "Cannot accept delivery: Payment not confirmed.")
        return redirect('staffs:my_deliveries')
    try:
        delivery.delivery_status = 'in_progress'
        delivery.save()
        messages.success(request, "Delivery accepted and is now in progress.")
        logger.info(f"Delivery {delivery_id} accepted by user {request.user.id}, status updated to in_progress")
        send_sms(
            delivery.phone_number,
            f"Your order #{delivery.id} has been accepted and is in progress. Delivery to: {delivery.address or delivery.get_predefined_address_display()}"
        )
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    return redirect('staffs:my_deliveries')

@login_required
@require_POST
def decline_delivery(request, delivery_id):
    delivery = get_object_or_404(DeliveryInfo, id=delivery_id)
    logger.info(f"User {request.user.id} attempting to decline delivery {delivery_id}, current status: {delivery.delivery_status}")

    assignment = StaffAssignment.objects.filter(staff=request.user, delivery=delivery).first()
    if not assignment:
        messages.error(request, "You are not assigned to this delivery.")
        logger.warning(f"User {request.user.id} not assigned to delivery {delivery_id}")
        return redirect('staffs:my_deliveries')

    if delivery.delivery_status == 'pending':
        reason = request.POST.get('decline_reason', '').strip()
        if not reason:
            messages.error(request, "Please provide a reason for declining the delivery.")
            logger.warning(f"Decline attempt for delivery {delivery_id} failed: No reason provided")
            return redirect('staffs:my_deliveries')

        try:
            delivery.delivery_status = 'cancelled'
            delivery.save()

            Notification.objects.create(
                recipient=request.user,
                message=f"Delivery declined: {reason}",
                related_delivery=delivery,
                notification_type='delivery_declined'
            )

            messages.info(request, "You declined the delivery.")
            logger.info(f"Delivery {delivery_id} declined by user {request.user.id}, status updated to cancelled, reason: {reason}")

            send_sms(
                delivery.phone_number,
                f"Your order #{delivery.id} has been cancelled. Reason: {reason}. Please contact support for assistance."
            )

        except Exception as e:
            messages.error(request, f"Error declining delivery: {str(e)}")
            logger.error(f"Error declining delivery {delivery_id}: {str(e)}")
    else:
        messages.warning(request, "This delivery cannot be declined as it is no longer pending.")
        logger.warning(f"Delivery {delivery_id} is not pending, status: {delivery.delivery_status}")

    return redirect('staffs:my_deliveries')

@login_required
@staff_view
def availability(request, staff_id=None):
    today = now().date()

    def get_user_status(user):
        if StaffAssignment.objects.filter(staff=user, delivery__created_at__date=today).exists():
            return 'delivering'
        elif user.last_login and user.last_login.date() == today:
            return 'present'
        return 'not at work'

    staff = request.user
    # Badge counts
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    if staff_id:
        staff = get_object_or_404(User, id=staff_id)
        if not (request.user.user_type in ['staff', 'admin'] or request.user.is_superuser):
            return render(request, 'staffs/error.html', {'message': 'You do not have permission to view this page.'})
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()
        context = {
            'staff': staff,
            'my_deliveries': {
                'active_count': StaffAssignment.objects.filter(
                    staff=staff,
                    delivery__delivery_status='in_progress'
                ).count()
            },
            'dashboard_notifications': dashboard_notifications,
            'history_notifications': history_notifications,
            'availability_notifications': availability_notifications,
        }
        return render(request, 'staffs/availability_single.html', context)

    if not (request.user.user_type in ['staff', 'admin'] or request.user.is_superuser):
        return render(request, 'staffs/error.html', {'message': 'You do not have permission to view this page.'})

    staff_list = User.objects.filter(user_type='staff')
    for staff in staff_list:
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()

    context = {
        'staff_list': staff_list,
        'my_deliveries': {
            'active_count': StaffAssignment.objects.filter(
                staff=request.user,
                delivery__delivery_status='in_progress'
            ).count()
        },
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
    }
    return render(request, 'staffs/availability.html', context)

@login_required
@staff_view
def profile(request):
    staff = request.user
    # Badge counts
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    context = {
        'my_deliveries': {
            'active_count': StaffAssignment.objects.filter(
                staff=staff,
                delivery__delivery_status='in_progress'
            ).count()
        },
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
    }
    return render(request, 'staffs/profile.html', context)

@login_required
@staff_view
def settings(request):
    staff = request.user
    # Badge counts
    dashboard_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type='new_order'
    ).count()
    history_notifications = Notification.objects.filter(
        recipient=staff,
        is_read=False,
        notification_type__in=['delivery_completed', 'delivery_declined']
    ).count()
    availability_notifications = StaffAssignment.objects.filter(
        staff=staff,
        assigned_at__gte=now().replace(hour=0, minute=0, second=0, microsecond=0),
        assigned_at__lt=now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    ).count()

    context = {
        'my_deliveries': {
            'active_count': StaffAssignment.objects.filter(
                staff=staff,
                delivery__delivery_status='in_progress'
            ).count()
        },
        'dashboard_notifications': dashboard_notifications,
        'history_notifications': history_notifications,
        'availability_notifications': availability_notifications,
    }
    return render(request, 'staffs/settings.html', context)

@login_required
@staff_view
def get_unread_notifications(request):
    unread = Notification.objects.filter(recipient=request.user, is_read=False).select_related('related_delivery').order_by('-created_at')
    notifications_data = [{
        'id': n.id,
        'message': n.message,
        'type': n.notification_type,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'delivery_id': n.related_delivery.id if n.related_delivery else None,
        'delivery_status': n.related_delivery.delivery_status if n.related_delivery else None,  # Add delivery status
    } for n in unread]
    return JsonResponse({'notifications': notifications_data})

@login_required
@staff_view
@require_POST
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if request.method == 'POST':
        notification.delete()
        return redirect('staffs:delivery_history')
    return redirect('staffs:delivery_history')

@login_required
@staff_view
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
@staff_view
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})
class DeliveryTrackingView(TemplateView):
    """Display active deliveries for tracking."""
    template_name = 'staffs/delivery_tracking.html'

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        staff = self.request.user
        context['active_deliveries'] = StaffAssignment.objects.filter(
            staff=staff, delivery__delivery_status='in_progress'
        ).select_related('delivery')
        context.update(get_badge_counts(staff))
        logger.debug(f"Delivery tracking rendered for staff {staff.id}")
        return context

@login_required
@staff_view
@require_POST
def update_driver_location(request, delivery_id: int):
    """Update the driver's location for a specific delivery (staff only)."""
    try:
        delivery = get_object_or_404(
            DeliveryInfo, id=delivery_id, staff_assignments__staff=request.user
        )
        data = json.loads(request.body)
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            logger.warning(f"Invalid coordinates for delivery {delivery_id}: lat={lat}, lng={lng}")
            return JsonResponse({'status': 'error', 'message': 'Invalid coordinates'}, status=400)

        delivery.driver_location = {'lat': lat, 'lng': lng}
        delivery.last_location_update = now()
        delivery.save()
        logger.info(f"Driver location updated for delivery {delivery_id} by staff {request.user.id}")
        return JsonResponse({'status': 'success'})
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid location data for delivery {delivery_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f"Invalid location data: {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Error updating driver location for delivery {delivery_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@staff_view
def get_delivery_locations(request, delivery_id: int):
    """Retrieve delivery locations for a specific delivery (staff access)."""
    try:
        delivery = get_object_or_404(
            DeliveryInfo, id=delivery_id, staff_assignments__staff=request.user
        )
        return JsonResponse({
            'status': 'success',
            'restaurant': delivery.restaurant_location or {'lat': -15.4167, 'lng': 28.2833},
            'driver': delivery.driver_location,
            'destination': {
                'address': delivery.address or delivery.get_predefined_address_display(),
            }
        })
    except DeliveryInfo.DoesNotExist:
        logger.warning(f"Delivery {delivery_id} not found for staff {request.user.id}")
        return JsonResponse({'status': 'error', 'message': 'Delivery not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching delivery locations for {delivery_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)