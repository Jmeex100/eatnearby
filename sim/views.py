import random
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from sim import views
from core.images import get_fastfood_photos, get_drinks_photos, get_restaurant_photos
from auths.models import Product


from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.templatetags.static import static
from django.contrib import messages
from .forms import ContactForm  # Import your form class



def menu_view(request):
    restaurant_photos = get_restaurant_photos()

    random.shuffle(restaurant_photos)
    context = {
      
        'fastfood_photos': get_fastfood_photos(),
        'drinks_photos': get_drinks_photos(),
        'restaurant_photos': get_restaurant_photos(),
    }
    return render(request, 'menu.html', context)




def home(request):
    restaurant_photos = get_restaurant_photos()
    random.shuffle(restaurant_photos)
    
    context = {
        'restaurant_photos': restaurant_photos,
    }
    return render(request, 'home.html', context)

import random
from django.shortcuts import render
from core.images import get_fastfood_photos, get_drinks_photos, get_restaurant_photos
from auths.models import Food, FastFood, Drink

def menu(request):
    # Get all products and order them by creation date
    foods = Food.objects.select_related('category').all()
    fastfoods = FastFood.objects.select_related('category').all()
    drinks = Drink.objects.select_related('category').all()

    # Shuffle photos without modifying the original list
    restaurant_photos = get_restaurant_photos()[:]
    drinks_photos = get_drinks_photos()[:]
    fastfood_photos = get_fastfood_photos()[:]
    random.shuffle(restaurant_photos)
    random.shuffle(drinks_photos)
    random.shuffle(fastfood_photos)

    context = {
        'foods': foods,
        'fastfoods': fastfoods,
        'drinks': drinks,
        'restaurant_photos': restaurant_photos,
        'drinks_photos': drinks_photos,
        'fastfood_photos': fastfood_photos,
    }
    return render(request, 'sim/menu.html', context)


def map(request):
    return render(request, 'sim/map.html')

def login(request):
    return render(request, 'auth/login_page.html')

def about(request):
    return render(request, 'sim/about.html')

# def signup(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         email = request.POST['email']
#         user = User.objects.create_user(
#                 username=username,
#                 password=password,
#                 email=email
#             )
#         login(request, user)
#         subject = "Welcome to Eats Nearby"
#         message = f"Hi {user.username}, thank you for registering with Eats Nearby."
#         email_from = settings.EMAIL_HOST_USER
#         recipient_list = [user.email]
#         send_mail(subject, message, email_from, recipient_list)
#         return redirect('contact')
#     return render(request, "sim/signup.html")

import logging

logger = logging.getLogger(__name__)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Create email
            email_subject = f"Contact Us Message from {name}"
            email_body = f"Message from: {name}\nEmail: {email}\n\n{message}"
            
            try:
                email = EmailMessage(
                    subject=email_subject,
                    body=email_body,
                    from_email=settings.EMAIL_HOST_USER,  # Use the configured email
                    to=['mulangarichard1000@gmail.com'],  # Replace with your actual email address
                )
                email.send()
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('contact')  # Redirect after successful form submission
            except Exception as e:
                logger.error(f'Error sending email: {e}')
                messages.error(request, f'There was an error sending your message: {e}')
                
    else:
        form = ContactForm()
        
    return render(request, 'sim/contact.html', {'form': form})
