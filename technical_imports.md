# Technical Import Statements for Eat Nearby Django Apps

## Generated Import Statements

Based on the analysis of the project structure and models, here are the import statements for each app as requested:

### 1. auths (Users + Products)
```python
from auths.models import User, Category, Product, FastFood, Food, Drink
```

### 2. sim (Frontend + PWA)
```python
from django.template.loader import get_template
from sim.views import home, menu, contact_view
from django.templatetags.static import static
```

### 3. community (Posts, Reviews, Recipes, Challenges, Q&A)
```python
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
```

### 4. cart (Cart + CartItem)
```python
from cart.models import Cart, CartItem
from django.db import models
```

### 5. payments (Delivery + Payment Systems)
```python
from payments.models import DeliveryInfo, PaymentHistory
from payments.cards import paypal, pesapal, stripe
from payments.mobile import airtel, mtn, zamtel
```

### 6. staffs (Staff Assignment + Notifications)
```python
from staffs.models import StaffServiceArea, StaffAssignment, Notification
```

### 7. superadmin (Admin Dashboard)
```python
from auths.models import User, Category, Product, FastFood, Food, Drink
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
from cart.models import Cart, CartItem
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification
from django.contrib.admin import ModelAdmin, site
```

## 🔥 ALL-IN-ONE Kilo Prompt (Imports for Entire Project)
```python
# All-in-one import statements for all Django apps in eatnearby project

# auths app imports
from auths.models import User, Category, Product, FastFood, Food, Drink

# sim app imports
from django.template.loader import get_template
from sim.views import home, menu, contact_view
from django.templatetags.static import static

# # Technical Import Statements for Eat Nearby Django Apps

## Generated Import Statements

Based on the analysis of the project structure and models, here are the import statements for each app as requested:

### 1. auths (Users + Products)
```python
from auths.models import User, Category, Product, FastFood, Food, Drink
```

### 2. sim (Frontend + PWA)
```python
from django.template.loader import get_template
from sim.views import home, menu, contact_view
from django.templatetags.static import static
```

### 3. community (Posts, Reviews, Recipes, Challenges, Q&A)
```python
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
```

### 4. cart (Cart + CartItem)
```python
from cart.models import Cart, CartItem
from django.db import models
```

### 5. payments (Delivery + Payment Systems)
```python
from payments.models import DeliveryInfo, PaymentHistory
from payments.cards import paypal, pesapal, stripe
from payments.mobile import airtel, mtn, zamtel
```

### 6. staffs (Staff Assignment + Notifications)
```python
from staffs.models import StaffServiceArea, StaffAssignment, Notification
```

### 7. superadmin (Admin Dashboard)
```python
from auths.models import User, Category, Product, FastFood, Food, Drink
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
from cart.models import Cart, CartItem
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification
from django.contrib.admin import ModelAdmin, site
```

## Full Code Snippets

### Register View (auths/views/auth_views.py)
```python
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from ..forms import CustomUserCreationForm
import secrets
import string

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
```

### Register Template (auths/templates/auths/register_page.html)
```html
{% extends 'base.html' %}
{% block title %}Register{% endblock %}

{% block content %}
<section class="min-h-screen flex py-8 items-center justify-center bg-gradient-to-r from-blue-50 to-purple-50">
    <div class="container mx-auto px-4 py-12 flex items-center justify-center">
        <div class="max-w-md w-full bg-white rounded-xl shadow-2xl p-8">
            <!-- Form Header -->
            <h2 class="text-3xl py-8 font-bold text-gray-800 mb-8 text-center">Create Your Account</h2>

            <!-- Messages Display -->
            {% if messages %}
                <div class="mb-6">
                    {% for message in messages %}
                        <div class="p-4 rounded-lg text-sm {% if message.tags == 'success' %}bg-green-100 text-green-700{% elif message.tags == 'error' %}bg-red-100 text-red-700{% elif message.tags == 'warning' %}bg-yellow-100 text-yellow-700{% else %}bg-blue-100 text-blue-700{% endif %}" role="alert">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}

            <!-- Form Start -->
            <form method="post" class="space-y-6">
                {% csrf_token %}

                <!-- Username -->
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                    <input
                        type="text"
                        name="username"
                        id="username"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        placeholder="Enter your username"
                        required
                    >
                    {% if form.username.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.username.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- First Name -->
                <div>
                    <label for="first_name" class="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                    <input
                        type="text"
                        name="first_name"
                        id="first_name"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        placeholder="Enter your first name"
                        required
                    >
                    {% if form.first_name.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.first_name.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- Last Name -->
                <div>
                    <label for="last_name" class="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                    <input
                        type="text"
                        name="last_name"
                        id="last_name"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        placeholder="Enter your last name"
                        required
                    >
                    {% if form.last_name.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.last_name.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- Email -->
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                        type="email"
                        name="email"
                        id="email"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        placeholder="Enter your email"
                        required
                    >
                    {% if form.email.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.email.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- User Type -->
                <div>
                    <label for="user_type" class="block text-sm font-medium text-gray-700 mb-2">User Type</label>
                    <select
                        name="user_type"
                        id="user_type"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        required
                    >
                        <option value="customer" selected>Customer</option>
                        <option value="admin">Admin</option>
                        <option value="staff">Staff</option>
                    </select>
                    {% if form.user_type.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.user_type.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- Gender -->
                <div>
                    <label for="gender" class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                    <select
                        name="gender"
                        id="gender"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                    >
                        <option value="" selected>Select gender</option>
                        <option value="mr">Mr.</option>
                        <option value="mrs">Mrs.</option>
                        <option value="miss">Miss</option>
                        <option value="ms">Ms.</option>
                    </select>
                    {% if form.gender.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.gender.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- Phone Number -->
                <div>
                    <label for="phone_number" class="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                    <input
                        type="text"
                        name="phone_number"
                        id="phone_number"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-300"
                        placeholder="Enter your phone number"
                    >
                    {% if form.phone_number.errors %}
                        <div class="text-red-600 text-sm mt-2">{{ form.phone_number.errors|striptags }}</div>
                    {% endif %}
                </div>

                <!-- Submit Button -->
                <button
                    type="submit"
                    class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-300"
                >
                    Register
                </button>

                <!-- Login Link -->
                <div class="text-center mt-6">
                    <p class="text-sm text-gray-600">
                        Already have an account?
                        <a href="{% url 'login' %}" class="text-blue-600 hover:text-blue-800 font-semibold transition duration-300">
                            Log in here
                        </a>
                    </p>
                </div>
            </form>
            <!-- Form End -->
        </div>
    </div>
</section>
{% endblock %}
```

### Restaurant List View (community/views/restaurants.py)
```python
from django.shortcuts import render
from ..models import Restaurant

def restaurant_list(request):
    """List all restaurants"""
    restaurants = Restaurant.objects.all().order_by('-created_at')
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})
```

### Restaurant List Template (community/templates/restaurant/restaurant_list.html)
```html
{% extends "community_base.html" %}
{% load static %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-800 dark:text-dark-text mb-6">Restaurants</h1>
    {% if messages %}
        {% for message in messages %}
            <div class="bg-red-100 text-red-700 p-4 rounded mb-4">{{ message }}</div>
        {% endfor %}
    {% else %}
        <p class="text-gray-600 dark:text-gray-300">No restaurant available. Please contact the administrator.</p>
    {% endif %}
</div>
{% endblock content %}
```

## 🔥 ALL-IN-ONE Kilo Prompt (Imports for Entire Project)
```python
# All-in-one import statements for all Django apps in eatnearby project

# auths app imports
from auths.models import User, Category, Product, FastFood, Food, Drink

# sim app imports
from django.template.loader import get_template
from sim.views import home, menu, contact_view
from django.templatetags.static import static

# community app imports
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer

# cart app imports
from cart.models import Cart, CartItem
from django.db import models

# payments app imports
from payments.models import DeliveryInfo, PaymentHistory
from payments.cards import paypal, pesapal, stripe
from payments.mobile import airtel, mtn, zamtel

# staffs app imports
from staffs.models import StaffServiceArea, StaffAssignment, Notification

# superadmin app imports
from auths.models import User, Category, Product, FastFood, Food, Drink
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
from cart.models import Cart, CartItem
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification
from django.contrib.admin import ModelAdmin, site app imports
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer

# cart app imports
from cart.models import Cart, CartItem
from django.db import models

# payments app imports
from payments.models import DeliveryInfo, PaymentHistory
from payments.cards import paypal, pesapal, stripe
from payments.mobile import airtel, mtn, zamtel

# staffs app imports
from staffs.models import StaffServiceArea, StaffAssignment, Notification

# superadmin app imports
from auths.models import User, Category, Product, FastFood, Food, Drink
from community.models import Restaurant, Post, Review, Challenge, Recipe, RestaurantQuestion, RestaurantAnswer
from cart.models import Cart, CartItem
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification
from django.contrib.admin import ModelAdmin, site