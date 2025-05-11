from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.template import TemplateDoesNotExist
from django.core.paginator import Paginator
from .models import Notification, StaffAssignment

from .staffs_decorator import staff_view
from payments.models import PaymentHistory, DeliveryInfo

User = get_user_model()

@login_required
@staff_view
def dashboard(request):
    today = now().date()
    staff = request.user

    # Aggregate delivery stats in one query
    stats = StaffAssignment.objects.filter(staff=staff).aggregate(
        active_count=Count('id', filter=Q(delivery__delivery_status='in_progress')),
        completed_today_count=Count('id', filter=Q(delivery__delivery_status='completed', delivery__updated_at__date=today)),
        total_completed_count=Count('id', filter=Q(delivery__delivery_status='completed'))
    )
    active_deliveries = stats['active_count']
    completed_today = stats['completed_today_count']
    total_completed = stats['total_completed_count']
    on_time_rate = 0 if total_completed == 0 else round((completed_today / total_completed) * 100)

    # Filter payment history for deliveries assigned to the staff
    payment_history = PaymentHistory.objects.filter(
        delivery_info__staff_assignments__staff=staff
    ).select_related('delivery_info').order_by('-created_at')
    paginator = Paginator(payment_history, 10)  # 10 payments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'my_deliveries': {
            'active_count': active_deliveries,
            'completed_today': completed_today,
            'on_time_rate': on_time_rate
        },
        'payment_history': page_obj,
        'page_obj': page_obj
    }
    try:
        return render(request, 'staffs/dashboard.html', context)
    except TemplateDoesNotExist:
        return render(request, 'staffs/error.html', {'message': 'Template not found.'})



@login_required
@staff_view
def my_deliveries(request):
    today = now().date()
    staff = request.user

    stats = StaffAssignment.objects.filter(staff=staff).aggregate(
        active_count=Count('id', filter=Q(delivery__delivery_status='in_progress')),
        completed_today_count=Count('id', filter=Q(delivery__delivery_status='completed', delivery__updated_at__date=today)),
        total_completed_count=Count('id', filter=Q(delivery__delivery_status='completed'))
    )
    active_deliveries = stats['active_count']
    completed_today = stats['completed_today_count']
    total_completed = stats['total_completed_count']
    on_time_rate = 0 if total_completed == 0 else round((completed_today / total_completed) * 100)

    context = {
        'my_deliveries': {
            'active_count': active_deliveries,
            'completed_today': completed_today,
            'on_time_rate': on_time_rate
        }
    }
    try:
        return render(request, 'staffs/my_deliveries.html', context)
    except TemplateDoesNotExist:
        return render(request, 'staffs/error.html', {'message': 'Template not found.'})
@login_required
@staff_view
def delivery_history(request):
    staff = request.user

    # Fetch deliveries assigned to the staff
    deliveries = DeliveryInfo.objects.filter(
        staff_assignments__staff=staff
    ).select_related('user').order_by('-updated_at')

    # Fetch notifications for the staff
    notifications = Notification.objects.filter(
        recipient=staff  # Use 'recipient' as per Notification model
    ).order_by('-created_at')[:10]  # Limit to recent 10 notifications

    context = {
        'deliveries': deliveries,
        'notifications': notifications
    }
    try:
        return render(request, 'staffs/delivery_history.html', context)
    except TemplateDoesNotExist:
        return render(request, 'staffs/error.html', {'message': 'Template not found.'})

@staff_view
def availability(request, staff_id=None):
    today = now().date()

    def get_user_status(user):
        if StaffAssignment.objects.filter(staff=user, delivery__created_at__date=today).exists():
            return 'delivering'
        elif user.last_login and user.last_login.date() == today:
            return 'present'
        return 'not at work'

    if staff_id:
        staff = get_object_or_404(User, id=staff_id)
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()
        return render(request, 'staffs/availability_single.html', {'staff': staff})

    staff_list = User.objects.filter(user_type='staff')
    for staff in staff_list:
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()

    return render(request, 'staffs/availability.html', {'staff_list': staff_list})

@staff_view
def profile(request):
    return render(request, 'staffs/profile.html')

@staff_view
def settings(request):
    return render(request, 'staffs/settings.html')

# ========== Notifications API ==========

@staff_view
def get_unread_notifications(request):
    unread = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    notifications_data = [{
        'id': n.id,
        'message': n.message,
        'type': n.notification_type,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'delivery_id': n.related_delivery.id if n.related_delivery else None,
    } for n in unread]
    return JsonResponse({'notifications': notifications_data})

@require_POST
@staff_view
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@require_POST
@staff_view
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def my_deliveries(request):
    context = {
        'my_deliveries': {
            'active_count': 3,
            'completed_today': 5,
            'on_time_rate': 92
        }
    }
    return render(request, 'staffs/my_deliveries.html', context)

@login_required
def delivery_history(request):
    return render(request, 'staffs/delivery_history.html')

@login_required
def availability(request, staff_id=None):
    today = now().date()

    # Helper function to determine user status
    def get_user_status(user):
        if StaffAssignment.objects.filter(staff=user, delivery__created_at__date=today).exists():
            return 'delivering'
        elif user.last_login and user.last_login.date() == today:
            return 'present'
        return 'not at work'

    if staff_id:
        # Fetch specific user (staff or admin) by ID
        staff = get_object_or_404(User, id=staff_id)
        # Restrict access: only staff, admins, or superusers can view
        if not (request.user.user_type in ['staff', 'admin'] or request.user.is_superuser):
            return render(request, 'staffs/error.html', {'message': 'You do not have permission to view this page.'})
        
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()
        return render(request, 'staffs/availability_single.html', {'staff': staff})

    # For all-staff view, allow staff, admins, or superusers
    if not (request.user.user_type in ['staff', 'admin'] or request.user.is_superuser):
        return render(request, 'staffs/error.html', {'message': 'You do not have permission to view this page.'})

    # Fetch all staff members
    staff_list = User.objects.filter(user_type='staff')
    for staff in staff_list:
        staff.status = get_user_status(staff)
        staff.role = getattr(staff, 'get_user_type_display', lambda: 'Staff')()

    return render(request, 'staffs/availability.html', {'staff_list': staff_list})

@login_required
def profile(request):
    return render(request, 'staffs/profile.html')

@login_required
def settings(request):
    return render(request, 'staffs/settings.html')

# ========== Notifications API ==========

@login_required
def get_unread_notifications(request):
    unread = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    notifications_data = [{
        'id': n.id,
        'message': n.message,
        'type': n.notification_type,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'delivery_id': n.related_delivery.id if n.related_delivery else None,
    } for n in unread]
    return JsonResponse({'notifications': notifications_data})

@require_POST
@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@require_POST
@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})