from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from functools import wraps

# Custom decorator to restrict access to staff, admins, or superusers
def staff_or_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.user_type in ['staff', 'admin'] or request.user.is_superuser):
            return render(request, 'staffs/error.html', {'message': 'You do not have permission to view this page.'})
        return view_func(request, *args, **kwargs)
    return wrapper

# Combine login_required and staff_or_admin_required
def staff_view(view_func):
    return login_required(staff_or_admin_required(view_func))