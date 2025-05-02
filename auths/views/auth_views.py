from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from ..forms import CustomUserCreationForm
from django.core.mail import EmailMessage
from django.conf import settings
import secrets  # For generating secure random passwords
import string

# ✅ Login View
def login_page(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('index')  # Redirect to the homepage or dashboard
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid form submission. Please check your inputs.')
    else:
        form = AuthenticationForm()
    return render(request, 'auths/login_page.html', {'form': form})

# ✅ Register View
def register_page(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don’t save yet, we need to set the password
            
            # Generate a random password
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for _ in range(12))  # 12-character random password
            user.set_password(password)  # Hash and set the password
            user.save()  # Now save the user with the password
            
        # Use a public URL for the logo
            logo_url = 'https://your-public-url.com/EatsNearbylogo.png'  # Replace with actual URL

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
            email.content_subtype = "html"  # Set the email content type to HTML
            
            try:
                email.send()
                messages.success(request, 'Registration successful! Check your email for your username and password.')
            except Exception as e:
                messages.warning(request, 'Registration successful, but we couldn’t send the welcome email.')
            
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please check your inputs.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auths/register_page.html', {'form': form})

# ✅ Logout View
def logout_page(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')