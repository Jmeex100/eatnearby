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

            subject = 'Welcome to CoreEat 🍴!'
            html_message = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #fff8f0; border-radius: 10px;">
                    <img src="{logo_url}" alt="Welcome to CoreEat" 
                        style="width: 100%; max-height: 200px; object-fit: cover; border-radius: 10px; margin-bottom: 20px;">
                    
                    <h1 style="color: #d84315; text-align: center;">Welcome, {user.first_name}! 🎉</h1>
                    
                    <p style="color: #444; font-size: 16px; text-align: center;">
                        Thanks for joining <strong>CoreEat</strong> — your gateway to tasty meals nearby!
                    </p>
                    
                    <div style="margin: 20px auto; padding: 15px; border: 1px solid #f1c40f; background: #fff3cd; border-radius: 8px; max-width: 400px;">
                        <p style="font-size: 16px; color: #333; margin: 8px 0;">
                            🍔 <strong>Username:</strong> {user.username}
                        </p>
                        <p style="font-size: 16px; color: #333; margin: 8px 0;">
                            🍕 <strong>Password:</strong> {password}
                        </p>
                    </div>

                    <p style="color: #d32f2f; font-weight: bold; text-align: center;">
                        Please log in and change your password for security 🔑
                    </p>
                    
                    <p style="color: #388e3c; text-align: center; font-size: 15px;">
                        Bon appétit,<br>The CoreEat Team 🍴
                    </p>
                    
                    <hr style="border: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #888; text-align: center;">
                        This is an automated message. Please do not reply.
                    </p>
                </div>
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
