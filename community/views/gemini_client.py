# community/views/gemini_client.py
import os
import json
import time
import logging
from datetime import datetime
import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg

from auths.models import User, Category, FastFood, Food, Drink
from community.models import (
    Restaurant, UserProfile, Post, Review, Comment, Challenge, ChallengeParticipation,
    Recipe, RecipeIngredient, RecipeInstruction, RecipeTag, RestaurantQuestion, RestaurantAnswer
)
from payments.models import DeliveryInfo, PaymentHistory
from staffs.models import StaffServiceArea, StaffAssignment, Notification

logger = logging.getLogger(__name__)

# ========= CONFIGURATION ========= #
API_KEYS = settings.GEMINI_KEYS
API_STATE_FILE = "api_state.json"
CHAT_HISTORY_FILE = "chat_history.json"

MAX_HISTORY = 20
ROTATION_LIMIT = 50
RETRY_LIMIT = 3


# ========= API STATE MANAGEMENT ========= #
def load_api_state():
    if os.path.exists(API_STATE_FILE):
        try:
            with open(API_STATE_FILE, "r") as f:
                state = json.load(f)
                if isinstance(state, dict):
                    return state
        except Exception as e:
            logger.warning(f"Failed to load API state: {e}")
    return {"current_key_index": 0, "usage_count": 0}


def save_api_state(state):
    try:
        with open(API_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save API state: {e}")


def rotate_api_key():
    """Rotate to the next API key"""
    state = load_api_state()
    next_index = (state.get("current_key_index", 0) + 1) % len(API_KEYS)
    state.update({"current_key_index": next_index, "usage_count": 0})
    save_api_state(state)
    logger.info(f"🔁 Rotated API key → Index {next_index}")
    return API_KEYS[next_index]


def get_current_api_key():
    """Retrieve API key with usage tracking and rotation"""
    state = load_api_state()
    index = state.get("current_key_index", 0)
    usage = state.get("usage_count", 0) + 1

    if usage >= ROTATION_LIMIT:
        return rotate_api_key()

    state.update({"usage_count": usage})
    save_api_state(state)

    return API_KEYS[index % len(API_KEYS)]


# ========= CHAT HISTORY ========= #
def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading chat history: {e}")
    return []


def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(history[-MAX_HISTORY:], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")


def build_context_prompt(history, prompt, db_data):
    context = (
        "You are EatNear BY Assistant, a helpful chatbot for a food community platform.\n"
        "Use the following database information to answer questions accurately. "
        "Do not reveal database structures or model names. "
        "Provide concise, natural, and user-friendly answers.\n\n"
        f"Database Information:\n{db_data}\n\n"
    )

    if history:
        context += "Previous conversation:\n"
        for msg in history[-5:]:
            role = "User" if msg["type"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"

    context += f"\nUser: {prompt}\nAssistant:"
    return context


# ========= DATABASE DATA FETCH ========= #
def get_db_data(user_prompt, user_type):
    db_data = ""

    # Restaurants
    if "restaurant" in user_prompt.lower() or "food place" in user_prompt.lower():
        restaurants = Restaurant.objects.filter(is_verified=True)[:5]
        db_data += "Top Restaurants:\n"
        for r in restaurants:
            avg_rating = Review.objects.filter(post__restaurant=r).aggregate(Avg('rating'))['rating__avg']
            db_data += f"- {r.name} ({r.city}) — {avg_rating or 'No'} stars\n"

    # Challenges
    if "challenge" in user_prompt.lower():
        challenges = Challenge.objects.filter(is_active=True)[:3]
        db_data += "\nActive Challenges:\n"
        for ch in challenges:
            db_data += f"- {ch.title}: {ch.description[:100]}...\n"

    # Recipes
    if "recipe" in user_prompt.lower() or "cook" in user_prompt.lower():
        recipes = Recipe.objects.all().order_by('-created_at')[:3]
        db_data += "\nRecent Recipes:\n"
        for rec in recipes:
            db_data += f"- {rec.title} ({rec.difficulty}) — {rec.servings} servings\n"

    # Posts
    if "post" in user_prompt.lower() or "review" in user_prompt.lower():
        posts = Post.objects.filter(is_published=True)[:3]
        db_data += "\nRecent Posts:\n"
        for p in posts:
            db_data += f"- {p.title} by {p.author.username}\n"

    # Comments
    if "comment" in user_prompt.lower():
        comments = Comment.objects.select_related('author', 'post')[:3]
        db_data += "\nRecent Comments:\n"
        for c in comments:
            db_data += f"- {c.author.username} commented on {c.post.title}: {c.content[:80]}\n"

    return db_data or "No relevant data found for the query."


# ========= GEMINI QUERY ========= #
def query_gemini(prompt):
    """Send a prompt to Gemini with retries, safety settings, and key rotation."""
    for attempt in range(RETRY_LIMIT):
        api_key = get_current_api_key()
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("models/gemini-2.0-flash")

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }

            response = model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=generation_config
            )

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise Exception(f"Response blocked: {response.prompt_feedback.block_reason}")

            if not response.text:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(1)
                    continue
                return "Sorry, I couldn’t generate a response right now."

            return response.text

        except Exception as e:
            err = str(e).lower()
            logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")

            if any(k in err for k in ["quota", "403", "429", "invalid", "limit", "api key", "block"]):
                logger.warning("⚠️ API key issue detected — rotating key")
                rotate_api_key()
                time.sleep(2)
            else:
                if attempt < RETRY_LIMIT - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2})")
                    time.sleep(1)
                else:
                    return f"Error: {str(e)}"


# ========= MAIN ENTRY ========= #
def get_gemini_response(user_prompt: str, user_type: str = 'guest') -> str:
    """Main entry function for the Django app."""
    history = load_chat_history()
    db_data = get_db_data(user_prompt, user_type)
    context_prompt = build_context_prompt(history, user_prompt, db_data)

    try:
        answer = query_gemini(context_prompt)
        history.append({"type": "user", "content": user_prompt, "time": datetime.now().isoformat()})
        history.append({"type": "assistant", "content": answer, "time": datetime.now().isoformat()})
        save_chat_history(history)
        return answer
    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return "Sorry, I had trouble processing your request. Please try again."
