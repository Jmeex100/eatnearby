# community/views/restaurants.py
import json
import time
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from auths.models import User
from ..forms import RestaurantForm
from ..models import (
    Restaurant,
    Post,
    RestaurantQuestion,
    Recipe,
    Challenge,
    UserProfile,
    Review,
    Comment,
)
from .gemini_client import get_gemini_response

# Set up logging
logger = logging.getLogger(__name__)
User = get_user_model()


# -----------------------------
# Helper functions
# -----------------------------
def is_staff(user):
    return user.is_authenticated and user.is_staff


# -----------------------------
# Public views
# -----------------------------
def restaurant_list(request):
    """List all restaurants"""
    restaurants = Restaurant.objects.all().order_by('-created_at')
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})


def restaurant(request):
    """Homepage section showing restaurants, posts, challenges, etc."""
    restaurants = Restaurant.objects.all()[:4]
    recent_posts = (
        Post.objects.filter(is_published=True)
        .select_related('author')
        .prefetch_related('comments', 'likes')[:3]
    )
    active_challenges = Challenge.objects.filter(is_active=True)[:2]
    popular_recipes = Recipe.objects.all().order_by('-created_at')[:3]
    top_foodies = UserProfile.objects.all().order_by('-user__post__count')[:5]
    recent_questions = (
        RestaurantQuestion.objects.all()
        .select_related('user', 'restaurant')
        .prefetch_related('answer')[:2]
    )
    featured_recipes = Recipe.objects.all()[:4]

    # Calculate top customers based on order count
    top_customers = (
        User.objects.filter(user_type='customer', paymenthistory__isnull=False)
        .annotate(order_count=Count('paymenthistory'))
        .order_by('-order_count')[:5]
    )

    context = {
        'restaurants': restaurants,
        'recent_posts': recent_posts,
        'active_challenges': active_challenges,
        'popular_recipes': popular_recipes,
        'top_foodies': top_foodies,
        'recent_questions': recent_questions,
        'featured_recipes': featured_recipes,
        'top_customers': top_customers,
    }
    return render(request, 'restaurant/restaurant.html', context)


def restaurant_detail(request, pk):
    """View a single restaurant’s details"""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    posts = (
        Post.objects.filter(restaurant=restaurant, is_published=True)
        .select_related('author', 'review')
        .order_by('-created_at')
    )
    questions = (
        RestaurantQuestion.objects.filter(restaurant=restaurant)
        .select_related('user', 'answer')
        .order_by('-created_at')
    )

    context = {
        'restaurant': restaurant,
        'posts': posts,
        'questions': questions,
    }
    return render(request, 'restaurant/restaurant_detail.html', context)


# -----------------------------
# Staff views (edit/delete)
# -----------------------------
@user_passes_test(is_staff)
def restaurant_edit(request, pk):
    """Edit a restaurant (staff only)"""
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
    """Delete a restaurant (staff only)"""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        messages.success(request, "Restaurant deleted successfully.")
        return redirect('community:restaurant-list')
    return render(request, 'restaurant/restaurant_confirm_delete.html', {'restaurant': restaurant})


# -----------------------------
# Chatbot view
# -----------------------------
@csrf_exempt
@require_POST
def chatbot(request):
    """
    EatNearBY Chatbot — retrieves contextual data from the DB and sends to Gemini.
    """
    try:
        data = json.loads(request.body)
        user_message = escape(data.get("message", "")).strip()
        user_type = data.get("user_type", "guest")

        if request.user.is_authenticated:
            user_type = getattr(request.user, "user_type", "guest")

        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        logger.info(f"🤖 Chatbot incoming message: {user_message} (User: {request.user if request.user.is_authenticated else 'Guest'})")

        # 🧠 Get Gemini response (includes DB data internally via get_db_data)
        response_text = get_gemini_response(user_message, user_type)

        # ✅ Optionally log user queries for analytics
        logger.info(f"Chatbot response generated for '{user_message}': {response_text[:100]}...")

        return JsonResponse({
            "response": response_text,
            "user_type": user_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON received in chatbot request.")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        logger.error(f"Chatbot internal error: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
