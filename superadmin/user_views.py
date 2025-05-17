from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from auths.models import User
from django.core.paginator import Paginator
from django.views.generic import DetailView
from .decorators import superadmin_required
from auths.forms import CustomUserCreationForm
from django.core.mail import EmailMessage
from django.conf import settings
import secrets
import string

# User List View
@superadmin_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/users/user_list.html', {'page_obj': page_obj})

# User Detail View
class UserDetailView(DetailView):
    model = User
    template_name = 'superadmin/users/user_detail.html'
    context_object_name = 'user'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.user_type == 'admin' and request.user.is_superuser):
            messages.error(request, "Access denied. Superadmin privileges required.")
            return redirect('login')  # Non-namespaced
        return super().dispatch(request, *args, **kwargs)

# User Create View
@superadmin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Generate a 12-character random password
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
            user.set_password(password)
            # Set superadmin-specific fields
            user_type = request.POST.get('user_type', 'customer')
            if user_type in ['admin', 'staff']:
                user.user_type = user_type
            if user_type == 'admin' and request.POST.get('is_superuser') == 'on':
                user.is_superuser = True
                user.is_staff = True
            user.save()

            # Send welcome email
            logo_url = request.build_absolute_uri('/static/images/logo/icon-192x192.png') if request.is_secure() else 'http://localhost:8000/static/images/logo/icon-192x192.png'
            subject = 'Welcome to Eat Nearby!'
            html_message = f"""
                <h1 style="color: #1a73e8;">Welcome, {user.first_name}!</h1>
                <img src="{logo_url}" alt="Eat Nearby Logo" style="max-width: 150px; height: auto; display: block; margin: 0 auto;">
                <p style="color: #333;">Your account has been created by an administrator.</p>
                <p style="font-size: 16px; color: #555;">
                    <strong style="color: #e91e63;">Username:</strong> {user.username}
                </p>
                <p style="font-size: 16px; color: #555;">
                    <strong style="color: #e91e63;">Password:</strong> {password}
                </p>
                <p style="color: #d32f2f; font-weight: bold;">Please log in with these credentials and change your password.</p>
                <p style="color: #388e3c;">Best regards,<br>The Eat Nearby Team</p>
                <hr style="border: 1px solid #ddd;">
                <p style="font-size: 12px; color: #888;">This is an automated message. Please do not reply.</p>
            """
            email = EmailMessage(
                subject,
                html_message,
                settings.EMAIL_HOST_USER,
                [user.email],
            )
            email.content_subtype = "html"
            try:
                email.send()
                messages.success(request, f'User {user.username} created successfully. Credentials sent to {user.email}.')
            except Exception as e:
                messages.warning(request, f'User created, but email failed to send: {str(e)}')
            return redirect('superadmin:user_list')
        else:
            messages.error(request, 'User creation failed. Please check your inputs.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'superadmin/users/user_form.html', {'form': form, 'action': 'Create'})

# User Update View
@superadmin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user_type = request.POST.get('user_type', user.user_type)
            if user_type in ['admin', 'staff']:
                user.user_type = user_type
            user.is_superuser = (user_type == 'admin' and request.POST.get('is_superuser') == 'on')
            user.is_staff = (user_type == 'admin' and user.is_superuser)
            user.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('superadmin:user_list')
        else:
            messages.error(request, 'User update failed. Please check your inputs.')
    else:
        form = CustomUserCreationForm(instance=user)
    return render(request, 'superadmin/users/user_form.html', {'form': form, 'action': 'Update', 'user': user})

# User Delete View
@superadmin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('superadmin:user_list')
        user.delete()
        messages.success(request, f'User {user.username} deleted successfully.')
        return redirect('superadmin:user_list')
    return render(request, 'superadmin/users/user_confirm_delete.html', {'user': user})

# Staff List View
@superadmin_required
def staff_list(request):
    staff = User.objects.filter(user_type='staff').order_by('-date_joined')
    paginator = Paginator(staff, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/users/staff_list.html', {'page_obj': page_obj})

# Customer List View
@superadmin_required
def customer_list(request):
    customers = User.objects.filter(user_type='customer').order_by('-date_joined')
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/users/customer_list.html', {'page_obj': page_obj})