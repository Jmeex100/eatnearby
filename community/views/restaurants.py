from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.conf import settings
from auths.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from ..forms import RestaurantForm
from ..models import Restaurant, Post, RestaurantQuestion, Recipe, Challenge, UserProfile
import requests
import json
import logging
from django.db.models import Count
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from ..forms import RestaurantForm
from ..models import Restaurant, Post, RestaurantQuestion, Recipe, Challenge, UserProfile
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Set up logging
logger = logging.getLogger(__name__)

# Helper to check if user is staff
def is_staff(user):
    return user.is_authenticated and user.is_staff

def restaurant(request):
    restaurants = Restaurant.objects.all()[:4]
    recent_posts = Post.objects.filter(is_published=True).select_related('author').prefetch_related('comments', 'likes')[:3]
    active_challenges = Challenge.objects.filter(is_active=True)[:2]
    popular_recipes = Recipe.objects.all().order_by('-created_at')[:3]
    top_foodies = UserProfile.objects.all().order_by('-user__post__count')[:5]
    recent_questions = RestaurantQuestion.objects.all().select_related('user', 'restaurant').prefetch_related('answer')[:2]
    featured_recipes = Recipe.objects.all()[:4]
    
    # Calculate top customers based on order count
    top_customers = User.objects.filter(
        user_type='customer',
        paymenthistory__isnull=False
    ).annotate(
        order_count=Count('paymenthistory')
    ).order_by('-order_count')[:5]

    context = {
        'restaurants': restaurants,
        'recent_posts': recent_posts,
        'active_challenges': active_challenges,
        'popular_recipes': popular_recipes,
        'top_foodies': top_foodies,
        'recent_questions': recent_questions,
        'featured_recipes': featured_recipes,
        'top_customers': top_customers,  # Add top_customers to context
    }
    return render(request, 'restaurant/restaurant.html', context)

# /home/surecode/Documents/Django/GitHub/eatnearby/community/views/restaurants.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from ..models import Restaurant, Recipe, Challenge
import json
import logging

from .gemini_client import get_gemini_response

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def chatbot(request):
    try:
        data = json.loads(request.body)
        user_message = escape(data.get("message", "")).strip()
        user_type = data.get("user_type", "guest")

        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        logger.info(f"Chatbot request: {user_message} (User Type: {user_type})")

        response_text = get_gemini_response(user_message, user_type)

        return JsonResponse({"response": response_text})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Chatbot error: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
def restaurant_list(request):
    try:
        restaurants = Restaurant.objects.all()
        if not restaurants.exists():
            messages.error(request, "No restaurants exist in the database. Please contact the administrator.")
            return render(request, 'restaurant/restaurant_list.html', {'restaurants': []})
        return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'restaurant/restaurant_list.html', {'restaurants': []})

def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    posts = Post.objects.filter(restaurant=restaurant, is_published=True).select_related('author', 'review').order_by('-created_at')
    questions = RestaurantQuestion.objects.filter(restaurant=restaurant).select_related('user', 'answer').order_by('-created_at')
    context = {
        'restaurant': restaurant,
        'posts': posts,
        'questions': questions,
    }
    return render(request, 'restaurant/restaurant_detail.html', context)

@user_passes_test(is_staff)
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, "Restaurant updated successfully.")
            return redirect('community:restaurant-detail', pk=restaurant.pk)
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_form.html', {'form': form, 'restaurant': restaurant})

@user_passes_test(is_staff)
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        messages.success(request, "Restaurant deleted successfully.")
        return redirect('community:restaurant-list')
    return render(request, 'restaurant/restaurant_confirm_delete.html', {'restaurant': restaurant})