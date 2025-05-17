from django.shortcuts import render, get_object_or_404
from staffs.models import Notification
from django.core.paginator import Paginator
from .decorators import superadmin_required

@superadmin_required
def notification_list(request):
    notifications = Notification.objects.all().order_by('-created_at')
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/notifications/notification_list.html', {'page_obj': page_obj})

@superadmin_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    return render(request, 'superadmin/notifications/notification_detail.html', {'notification': notification})