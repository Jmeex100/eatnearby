from django.shortcuts import redirect
from django.contrib import messages

def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.user_type == 'admin' and request.user.is_superuser):
            messages.error(request, "Access denied. Superadmin privileges required.")
            return redirect('login')  
        return view_func(request, *args, **kwargs)
    return wrapper