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
from payments.models import DeliveryInfo
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
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from auths.forms import CustomUserCreationForm
from auths.models import User
from cart.models import Cart
from payments.models import DeliveryInfo
from django.conf import settings
from django.core.mail import EmailMessage
import secrets
import string

logger = logging.getLogger(__name__)

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
            user_type = form.cleaned_data.get('user_type', 'customer')
            if user_type in ['admin', 'staff']:
                user.user_type = user_type
            if user_type == 'admin' and request.POST.get('is_superuser') == 'on':
                user.is_superuser = True
                user.is_staff = True
            user.save()  # Ensure user is saved
            logger.debug(f"User {user.username} saved with PK: {user.pk}")

            # Create DeliveryInfo for customers
            if user_type == 'customer':
                preferred_delivery_point = form.cleaned_data.get('preferred_delivery_point')
                if preferred_delivery_point:
                    try:
                        # Ensure cart is saved
                        cart, created = Cart.objects.get_or_create(user=user)
                        logger.debug(f"Cart for {user.username} - Created: {created}, PK: {cart.pk}")
                        if created:
                            cart.save()  # Explicitly save if newly created
                            logger.debug(f"Cart saved with PK: {cart.pk}")
                        if not cart.pk:
                            raise ValueError(f"Cart for user {user.username} was not saved properly")
                        DeliveryInfo.objects.create(
                            user=user,
                            cart=cart,
                            predefined_address=preferred_delivery_point,
                            phone_number=form.cleaned_data.get('phone_number', ''),
                            delivery_status='pending',
                            payment_method='cash',
                        )
                        logger.debug(f"DeliveryInfo created for user {user.username}")
                    except Exception as e:
                        logger.error(f"Failed to set delivery info for user {user.username}: {str(e)}")
                        messages.warning(request, f'User created, but failed to set delivery info: {str(e)}')

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
                logger.error(f"Failed to send email to {user.email}: {str(e)}")
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
            user_type = form.cleaned_data.get('user_type', user.user_type)
            if user_type in ['admin', 'staff']:
                user.user_type = user_type
            user.is_superuser = (user_type == 'admin' and request.POST.get('is_superuser') == 'on')
            user.is_staff = (user_type == 'admin' and user.is_superuser)
            user.save()

            # Update or create DeliveryInfo for customers
            if user_type == 'customer':
                preferred_delivery_point = form.cleaned_data.get('preferred_delivery_point')
                if preferred_delivery_point:
                    try:
                        from cart.models import Cart
                        cart, _ = Cart.objects.get_or_create(user=user)
                        delivery_info, created = DeliveryInfo.objects.get_or_create(
                            user=user,
                            defaults={
                                'cart': cart,
                                'predefined_address': preferred_delivery_point,
                                'phone_number': form.cleaned_data.get('phone_number', ''),
                                'delivery_status': 'pending',
                                'payment_method': 'cash',
                            }
                        )
                        if not created and delivery_info.predefined_address != preferred_delivery_point:
                            delivery_info.predefined_address = preferred_delivery_point
                            delivery_info.phone_number = form.cleaned_data.get('phone_number', '')
                            delivery_info.save()
                    except Exception as e:
                        messages.warning(request, f'User updated, but failed to set delivery info: {str(e)}')
            else:
                # Remove DeliveryInfo for non-customers
                DeliveryInfo.objects.filter(user=user).delete()

            # Send update notification email
            logo_url = request.build_absolute_uri('/static/images/logo/icon-192x192.png') if request.is_secure() else 'http://localhost:8000/static/images/logo/icon-192x192.png'
            subject = 'Your Eat Nearby Account Has Been Updated'
            html_message = f"""
                <h1 style="color: #1a73e8;">Account Update Notification</h1>
                <img src="{logo_url}" alt="Eat Nearby Logo" style="max-width: 150px; height: auto; display: block; margin: 0 auto;">
                <p style="color: #333;">Dear {user.first_name},</p>
                <p style="color: #555;">Your account details have been updated by an administrator.</p>
                <p style="font-size: 16px; color: #555;">
                    <strong style="color: #e91e63;">Username:</strong> {user.username}<br>
                    <strong style="color: #e91e63;">User Type:</strong> {user.user_type}<br>
                    <strong style="color: #e91e63;">Email:</strong> {user.email}
                </p>
                <p style="color: #d32f2f; font-weight: bold;">Please log in to review your updated account details.</p>
                <p style="color: #388e3c;">Best regards,<br>The Eat Nearby Team</p>
                <hr style="border: 1px solid #ddd;">
 проявление <p style="font-size: 12px; color: #888;">This is an automated message. Please do not reply.</p>
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
                messages.success(request, f'User {user.username} updated successfully. Notification sent to {user.email}.')
            except Exception as e:
                messages.warning(request, f'User updated, but email failed to send: {str(e)}')

            return redirect('superadmin:user_list')
        else:
            messages.error(request, 'User update failed. Please check your inputs.')
    else:
        form = CustomUserCreationForm(instance=user)
        # Pre-populate preferred_delivery_point from DeliveryInfo if it exists
        try:
            delivery_info = DeliveryInfo.objects.filter(user=user).first()
            if delivery_info and delivery_info.predefined_address:
                form.initial['preferred_delivery_point'] = delivery_info.predefined_address
        except DeliveryInfo.DoesNotExist:
            pass
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