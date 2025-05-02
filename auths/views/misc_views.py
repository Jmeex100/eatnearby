from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.contrib import messages
from sim.forms import ContactForm  # Assuming you have a ContactForm in forms.py
from django.conf import settings
import logging
import random
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from sim import views
from core.images import get_fastfood_photos, get_drinks_photos, get_restaurant_photos

logger = logging.getLogger(__name__)

# ✅ Help View
def help_page(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            email_subject = f"Help Request from {name}"
            email_body = f"From: {name}\nEmail: {email}\n\n{message}"
            
            try:
                email = EmailMessage(
                    subject=email_subject,
                    body=email_body,
                    from_email=settings.EMAIL_HOST_USER,
                    to=['support@example.com'],
                )
                email.send()
                messages.success(request, 'Help request sent!')
                return redirect('help')
            except Exception as e:
                logger.error(f"Error sending email: {e}")
                messages.error(request, f"Error sending help request: {e}")
    else:
        form = ContactForm()
    return render(request, 'auths/help.html', {'form': form})

# ✅ Homepage View



def index(request):
    # Get the logged-in user's details
    if request.user.is_authenticated:
        user_name = request.user.last_name
        gender_prefix = request.user.get_gender_display() if request.user.gender else "Guest"
    else:
        user_name = "Guest"
        gender_prefix = "Guest"
    
    # Fetch photos (assuming these functions are defined elsewhere)
    restaurant_photos = get_restaurant_photos()
    fastfood_photos = get_fastfood_photos()
    drinks_photos = get_drinks_photos()
    
    # Shuffle photos for variety
    random.shuffle(restaurant_photos)
    random.shuffle(fastfood_photos)
    random.shuffle(drinks_photos)
    
    # Pass data to the template
    context = {
        'user_name': user_name,
        'gender_prefix': gender_prefix,  # Add gender prefix to context
        'restaurant_photos': restaurant_photos,
        'fastfood_photos': fastfood_photos,
        'drinks_photos': drinks_photos,
    }
    return render(request, 'auths/index.html', context)