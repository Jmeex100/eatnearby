from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from ..forms import CustomUserCreationForm
import secrets
import string

# ✅ Login View
def login_page(request):
    """
    Handle user login using Django's AuthenticationForm.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('index')
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid form submission. Please check your inputs.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auths/login_page.html', {'form': form})


# ✅ Register View
def register_page(request):
    """
    Handle user registration with random password generation and welcome email.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Generate a 12-character random password
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
            user.set_password(password)
            user.save()

            # Use request.build_absolute_uri if available, fallback to a default
            if request.is_secure():
                logo_url = request.build_absolute_uri('/static/images/logo/icon-192x192.png')
            else:
                logo_url = 'http://localhost:8000/static/images/logo/icon-192x192.png'

            subject = 'Welcome to CoreEat!'
            html_message = f"""
                <h1 style="color: #1a73e8;">Welcome, {user.first_name}!</h1>
                <img src="{logo_url}" alt="CoreEat Logo" style="max-width: 150px; height: auto; display: block; margin: 0 auto;">
                <p style="color: #333;">Thank you for registering with <strong>CoreEat</strong>! Your account has been successfully created.</p>
                <p style="font-size: 16px; color: #555;">
                    <strong style="color: #e91e63;">Username:</strong> {user.username}
                </p>
                <p style="font-size: 16px; color: #555;">
                    <strong style="color: #e91e63;">Password:</strong> {password}
                </p>
                <p style="color: #d32f2f; font-weight: bold;">Please log in with these credentials and change your password for security.</p>
                <p style="color: #388e3c;">Best regards,<br>The CoreEat Team</p>
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
                messages.success(request, 'Registration successful! Check your email for login credentials.')
            except Exception as e:
                messages.warning(request, f'Registration successful, but email failed to send. ({str(e)})')

            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please check your inputs.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'auths/register_page.html', {'form': form})


# ✅ Logout View
def logout_page(request):
    """
    Log the user out and redirect to login page.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')
