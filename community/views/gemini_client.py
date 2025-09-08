# community/views/gemini_client.py
import os
import json
import logging
from datetime import datetime
import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg
from auths.models import User, Category, FastFood, Food, Drink
from community.models import (
    Restaurant, UserProfile, Post, Review, Comment, Challenge, ChallengeParticipation,
    Recipe, RecipeIngredient, RecipeInstruction, RecipeTag, RestaurantQuestion,
    RestaurantAnswer
)
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification

logger = logging.getLogger(__name__)

API_KEYS = settings.GEMINI_KEYS
API_STATE_FILE = "api_state.json"
CHAT_HISTORY_FILE = "chat_history.json"

def load_api_state():
    try:
        if os.path.exists(API_STATE_FILE):
            with open(API_STATE_FILE, "r") as f:
                state = json.load(f)
                if (
                    isinstance(state, dict)
                    and "current_key_index" in state
                    and "usage_count" in state
                ):
                    return state
    except Exception:
        pass
    return {"current_key_index": 0, "usage_count": 0}

def save_api_state(state):
    try:
        with open(API_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save API state: {e}")

def get_next_api_key():
    state = load_api_state()
    current_index = state["current_key_index"]
    usage_count = state["usage_count"] + 1

    if usage_count >= 50 or current_index >= len(API_KEYS):
        next_index = (current_index + 1) % len(API_KEYS)
        usage_count = 1
        logger.warning(f"Rotating API key: {current_index} -> {next_index}")
    else:
        next_index = current_index

    new_state = {"current_key_index": next_index, "usage_count": usage_count}
    save_api_state(new_state)
    return API_KEYS[next_index]

def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")

def build_context_prompt(history, new_prompt, db_data):
    context = "You are EatNear BY Assistant, a helpful chatbot for a food community platform. Use the following database information to answer questions accurately. Do not reveal the raw database structure or mention table names directly in your response. Provide concise, natural, and user-friendly answers based on the data and user query.\n\n"

    context += "Database Information:\n"
    context += db_data + "\n\n"

    if history:
        context += "Previous conversation:\n"
        for msg in history:
            role = "User" if msg["type"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
    context += f"\nUser: {new_prompt}\nAssistant:"
    return context

def get_db_data(user_prompt, user_type):
    """Fetch relevant data from all database tables based on the user prompt."""
    db_data = ""

    # Restaurants
    restaurants = Restaurant.objects.filter(is_verified=True)[:5]
    if "restaurant" in user_prompt.lower() or "food place" in user_prompt.lower():
        db_data += "Restaurants:\n"
        for restaurant in restaurants:
            avg_rating = Review.objects.filter(post__restaurant=restaurant).aggregate(Avg('rating'))['rating__avg']
            db_data += f"- {restaurant.name} in {restaurant.city}, {restaurant.country}. Description: {restaurant.description or 'No description'}. "
            db_data += f"Average Rating: {avg_rating:.1f} stars" if avg_rating else "No reviews yet"
            db_data += f". Website: {restaurant.website or 'N/A'}.\n"

    # Posts
    posts = Post.objects.filter(is_published=True)[:3]
    if "post" in user_prompt.lower() or "community" in user_prompt.lower():
        db_data += "Recent Community Posts:\n"
        for post in posts:
            db_data += f"- {post.title} by {post.author.username} ({post.get_post_type_display()}). Content: {post.content[:100]}... "
            db_data += f"Restaurant: {post.restaurant.name if post.restaurant else 'N/A'}. Likes: {post.likes.count()}.\n"

    # Reviews
    reviews = Review.objects.select_related('post__restaurant')[:3]
    if "review" in user_prompt.lower():
        db_data += "Recent Reviews:\n"
        for review in reviews:
            db_data += f"- {review.post.title} for {review.post.restaurant.name if review.post.restaurant else 'N/A'}. "
            db_data += f"Rating: {review.rating} stars. Food: {review.food_rating or 'N/A'}, Service: {review.service_rating or 'N/A'}, Ambiance: {review.ambiance_rating or 'N/A'}.\n"

    # Challenges
    challenges = Challenge.objects.filter(is_active=True)[:3]
    if "challenge" in user_prompt.lower():
        db_data += "Active Challenges:\n"
        for challenge in challenges:
            db_data += f"- {challenge.title}: {challenge.description[:100]}... Starts: {challenge.start_date}, Ends: {challenge.end_date}. "
            db_data += f"Participants: {challenge.participants.count()}.\n"

    # Recipes
    recipes = Recipe.objects.filter(is_published=True)[:3]
    if "recipe" in user_prompt.lower():
        db_data += "Popular Recipes:\n"
        for recipe in recipes:
            tags = ", ".join([tag.name for tag in recipe.tags.all()])
            db_data += f"- {recipe.title} by {recipe.author.username}. Difficulty: {recipe.get_difficulty_display()}. "
            db_data += f"Prep: {recipe.prep_time} mins, Cook: {recipe.cook_time} mins, Servings: {recipe.servings}. Tags: {tags or 'None'}.\n"

    # Recipe Ingredients and Instructions
    if "ingredient" in user_prompt.lower() or "instruction" in user_prompt.lower():
        recipe = Recipe.objects.filter(is_published=True).first()
        if recipe:
            db_data += f"Sample Recipe Details for {recipe.title}:\n"
            ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            db_data += "Ingredients:\n"
            for ing in ingredients:
                db_data += f"- {ing.quantity} {ing.name} ({ing.notes or 'No notes'})\n"
            instructions = RecipeInstruction.objects.filter(recipe=recipe)
            db_data += "Instructions:\n"
            for ins in instructions:
                db_data += f"- Step {ins.step_number}: {ins.instruction[:100]}...\n"

    # Restaurant Questions and Answers
    questions = RestaurantQuestion.objects.filter(is_answered=True)[:3]
    if "question" in user_prompt.lower() or "ask chef" in user_prompt.lower():
        db_data += "Recent Q&A:\n"
        for question in questions:
            answer = question.answer.answer if hasattr(question, 'answer') else 'No answer yet'
            db_data += f"- Question to {question.restaurant.name} by {question.user.username}: {question.question[:100]}... "
            db_data += f"Answer: {answer[:100]}...\n"

    # Categories and Products (FastFood, Food, Drink)
    if "menu" in user_prompt.lower() or "food" in user_prompt.lower() or "drink" in user_prompt.lower():
        categories = Category.objects.all()[:3]
        db_data += "Menu Categories and Products:\n"
        for category in categories:
            db_data += f"- Category: {category.name}\n"
            for model in [FastFood, Food, Drink]:
                products = model.objects.filter(category=category)[:2]
                for product in products:
                    db_data += f"  - {product.name} ({model.__name__}): ${product.price}, Quantity: {product.quantity}, Description: {product.description or 'N/A'}\n"

    # Delivery Info
    if user_type in ['staff', 'admin'] and "delivery" in user_prompt.lower():
        deliveries = DeliveryInfo.objects.filter(delivery_status__in=['pending', 'in_progress'])[:3]
        db_data += "Pending/In-Progress Deliveries:\n"
        for delivery in deliveries:
            db_data += f"- Delivery ID: {delivery.id} for {delivery.user.username}. Status: {delivery.get_delivery_status_display()}. "
            db_data += f"Address: {delivery.address or delivery.get_predefined_address_display()}. Payment: {delivery.get_payment_method_display()}.\n"

    # Payment History
    if user_type == 'admin' and "payment" in user_prompt.lower():
        payments = PaymentHistory.objects.all()[:3]
        db_data += "Recent Payments:\n"
        for payment in payments:
            db_data += f"- Payment by {payment.user.username} on {payment.created_at}: ${payment.total}. Items: {json.dumps(payment.items)[:100]}...\n"

    # Staff Service Areas and Assignments
    if user_type in ['staff', 'admin'] and ("delivery" in user_prompt.lower() or "assignment" in user_prompt.lower()):
        service_areas = StaffServiceArea.objects.all()[:3]
        db_data += "Staff Service Areas:\n"
        for area in service_areas:
            db_data += f"- {area.staff.username} covers {area.get_point_display()}.\n"
        assignments = StaffAssignment.objects.all()[:3]
        db_data += "Staff Assignments:\n"
        for assignment in assignments:
            db_data += f"- {assignment.staff.username} assigned to Delivery {assignment.delivery.id} at {assignment.assigned_at}.\n"

    # Notifications
    if user_type in ['staff', 'admin'] and "notification" in user_prompt.lower():
        notifications = Notification.objects.filter(is_read=False)[:3]
        db_data += "Unread Notifications:\n"
        for notification in notifications:
            db_data += f"- {notification.get_notification_type_display()} for {notification.recipient.username}: {notification.message[:100]}...\n"

    # User Profiles
    if "profile" in user_prompt.lower():
        profiles = UserProfile.objects.all()[:3]
        db_data += "User Profiles:\n"
        for profile in profiles:
            fav_restaurants = ", ".join([r.name for r in profile.favorite_restaurants.all()])
            db_data += f"- {profile.user.username}: Bio: {profile.bio or 'N/A'}. Dietary Preferences: {profile.dietary_preferences or 'None'}. "
            db_data += f"Favorite Restaurants: {fav_restaurants or 'None'}.\n"

    return db_data if db_data else "No relevant data found for the query."

def get_gemini_response(user_prompt: str, user_type: str = 'guest') -> str:
    history = load_chat_history()
    db_data = get_db_data(user_prompt, user_type)
    context_prompt = build_context_prompt(history, user_prompt, db_data)

    api_key = get_next_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        response = model.generate_content(context_prompt)

        history.append({"type": "user", "content": user_prompt, "time": datetime.now().isoformat()})
        history.append({"type": "assistant", "content": response.text, "time": datetime.now().isoformat()})

        if len(history) > 20:
            history = history[-20:]

        save_chat_history(history)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return "Sorry, I had trouble processing your request. Please try again."