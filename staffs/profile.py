from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views import get_notification_count

@login_required
def staff_list(request):
    return render(request, 'staffs/staff_list.html', {'new_order_count': get_notification_count()})

@login_required
def profile(request):
    return render(request, 'staffs/profile.html', {'new_order_count': get_notification_count()})

@login_required
def settings(request):
    return render(request, 'staffs/settings.html', {'new_order_count': get_notification_count()})
# staffs/profile.py