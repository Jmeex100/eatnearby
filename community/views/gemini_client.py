"""
EatNearBY AI Assistant using OpenRouter API
Balanced version: Factual for database queries, creative for general questions
"""

import os
import json
import requests
import logging
from datetime import datetime
from django.conf import settings
from django.db.models import Avg, Count, Sum, Max, Min, Q
from django.db import connection, models

from auths.models import User, Category, FastFood, Food, Drink
from community.models import (
    Restaurant, UserProfile, Post, Review, Comment, Challenge, ChallengeParticipation,
    Recipe, RecipeIngredient, RecipeInstruction, RecipeTag, RestaurantQuestion, RestaurantAnswer
)

logger = logging.getLogger(__name__)

# ========= CONFIGURATION ========= #
API_KEYS = settings.OPENROUTER_KEYS  # Update this in settings.py
API_STATE_FILE = "api_state.json"
CHAT_HISTORY_FILE = "chat_history.json"
MODEL = "openai/gpt-4.1-mini"  # Free/low-cost model
MAX_TOKENS = 1200  # Increased for better formatting
MAX_HISTORY = 10  # Keep last 10 conversations for context
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


# ========= EATNEARBY INFORMATION ========= #
def get_platform_info():
    """Get information about the EatNearBY platform"""
    info = """🏪 **About EatNearBY Platform:**

**What is EatNearBY?**
EatNearBY is a comprehensive food community platform that connects restaurants near Evelyn Hone College with customers through online food ordering, restaurant discovery, and community engagement.

**Main Objective:**
To create a simple and user-friendly platform that helps connect restaurants with their customers by making it easier to order food online, find restaurant details, and build stronger relationships between restaurants and customers.

**Specific Objectives:**
1. **Build stronger connections** between customers and SMEs (Small & Medium Enterprises)
2. **Provide a clear and engaging** online food ordering experience
3. **Simplify payment and order management** for both customers and SMEs
4. **Create a food community** where users can share experiences, recipes, and participate in challenges
5. **Support local restaurants** by providing them with digital tools to grow their business

**Key Features:**
- 📱 **Online Food Ordering** - Order from local restaurants
- 🏪 **Restaurant Discovery** - Find and explore nearby restaurants
- 👥 **Community Engagement** - Share posts, reviews, and recipes
- 🏆 **Food Challenges** - Participate in culinary competitions
- 📝 **Recipe Sharing** - Share and discover new recipes
- 💬 **Q&A System** - Ask questions to restaurant chefs
- 📊 **Admin Dashboard** - Manage restaurants, products, and users

**Target Users:**
- **Customers** - Order food, explore restaurants, join community
- **Restaurant Staff** - Manage menus, answer questions, post updates
- **Administrators** - Manage platform, moderate content, view analytics
- **SME Owners** - Grow their business through digital presence

**Location Focus:**
Primarily serving restaurants and customers around Evelyn Hone College area in Zambia, with expansion capabilities.

**Currency:**
All transactions are in **Zambian Kwacha (K)** - supporting local economy."""
    
    return info


# ========= DATABASE QUERY FUNCTIONS ========= #
def format_price_kwacha(price):
    """Format price as Zambian Kwacha (K)"""
    try:
        if price is None:
            return "K0.00"
        # Ensure price is Decimal or float
        price_value = float(price)
        return f"K{price_value:,.2f}"
    except:
        return "K0.00"


def get_food_for_budget(budget):
    """Get food items within a specific budget"""
    try:
        foods = Food.objects.filter(price__lte=budget).order_by('-price')
        
        if not foods:
            # Get the cheapest item available
            cheapest = Food.objects.order_by('price').first()
            if cheapest:
                return f"With K{budget}, you could get **{cheapest.name}** ({format_price_kwacha(cheapest.price)})."
            return f"No food items found within K{budget} budget."
        
        info = f"🍽️ **💰 Options for K{budget} Budget:**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, food in enumerate(foods[:5], 1):  # Show top 5
            price_formatted = format_price_kwacha(food.price)
            remaining = budget - food.price
            
            info += f"**{i}. {food.name}**\n"
            info += f"   💰 **Price:** {price_formatted}\n"
            info += f"   📦 **Stock:** {food.quantity} units\n"
            info += f"   🏷️  **Category:** {food.category.name}\n"
            
            if remaining > 0:
                info += f"   💸 **Remaining:** K{remaining:.2f}\n"
            
            info += "\n"
        
        # Add combination suggestions
        affordable_items = Food.objects.filter(price__lte=budget/2).order_by('price')
        if len(affordable_items) >= 2:
            info += "💡 **Combo Suggestions:**\n"
            combo1 = affordable_items[0]
            combo2 = affordable_items[1] if len(affordable_items) > 1 else affordable_items[0]
            total = combo1.price + combo2.price
            
            if total <= budget:
                info += f"• **{combo1.name}** + **{combo2.name}** = {format_price_kwacha(total)}\n"
        
        return info
    except Exception as e:
        logger.error(f"Error fetching food for budget: {e}")
        return "Unable to fetch budget options at the moment."


def get_all_food_items_formatted():
    """Get ALL food items with beautiful formatting"""
    try:
        foods = Food.objects.select_related('category').all().order_by('name')
        
        if not foods:
            return "No food items found in the database."
        
        info = "🍽️ **📋 All Food Items Menu**\n\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, food in enumerate(foods, 1):
            price_formatted = format_price_kwacha(food.price)
            
            info += f"**{i}. {food.name}**\n"
            info += f"   💰 **Price:** {price_formatted}\n"
            info += f"   🏷️  **Category:** {food.category.name}\n"
            info += f"   📦 **Stock:** {food.quantity} units\n"
            
            if food.description:
                desc = food.description.strip()
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                info += f"   📝 **Description:** {desc}\n"
            
            info += "\n"
        
        # Add summary
        total_items = foods.count()
        avg_price = sum(food.price for food in foods) / total_items if total_items > 0 else 0
        
        info += "📊 **📈 Quick Stats:**\n"
        info += f"• **Total Items:** {total_items}\n"
        info += f"• **Average Price:** {format_price_kwacha(avg_price)}\n"
        info += f"• **Price Range:** {format_price_kwacha(min(f.price for f in foods))} - {format_price_kwacha(max(f.price for f in foods))}\n"
        
        return info
    except Exception as e:
        logger.error(f"Error fetching food items: {e}")
        return "Unable to fetch food items at the moment."


def get_food_recommendations():
    """Get food recommendations based on different criteria"""
    try:
        info = "🍽️ **🌟 Food Recommendations**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Most popular (by stock quantity - assuming more stock = more popular)
        popular = Food.objects.order_by('-quantity')[:3]
        if popular:
            info += "**🔥 Popular Choices:**\n"
            for food in popular:
                info += f"• **{food.name}** - {format_price_kwacha(food.price)} ({food.quantity} available)\n"
            info += "\n"
        
        # Best value (low price, good quantity)
        best_value = Food.objects.filter(quantity__gt=10).order_by('price')[:3]
        if best_value:
            info += "**💸 Best Value:**\n"
            for food in best_value:
                info += f"• **{food.name}** - {format_price_kwacha(food.price)} (Great price!)\n"
            info += "\n"
        
        # Traditional Zambian dishes
        traditional = Food.objects.filter(category__name__icontains='traditional')[:3]
        if traditional:
            info += "🇿🇲 **Traditional Zambian:**\n"
            for food in traditional:
                info += f"• **{food.name}** - {format_price_kwacha(food.price)}\n"
            info += "\n"
        
        info += "💡 **Tips:**\n"
        info += "• Ask me 'what can I get for K50?' for budget options\n"
        info += "• Try 'show me cheap food' for affordable choices\n"
        info += "• Use 'traditional food' for local Zambian dishes\n"
        
        return info
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        return "Unable to fetch recommendations at the moment."


def get_cheap_food_options():
    """Get cheap/affordable food options"""
    try:
        # Get food under K50
        cheap_foods = Food.objects.filter(price__lt=50).order_by('price')
        
        if not cheap_foods:
            # If nothing under K50, get cheapest 5 items
            cheap_foods = Food.objects.order_by('price')[:5]
        
        if not cheap_foods:
            return "No food items found."
        
        info = "🍽️ **💸 Affordable Food Options**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        info += "**💰 Budget-Friendly Picks:**\n"
        for i, food in enumerate(cheap_foods, 1):
            price_formatted = format_price_kwacha(food.price)
            info += f"{i}. **{food.name}** - {price_formatted}\n"
            info += f"   Category: {food.category.name} | Stock: {food.quantity}\n\n"
        
        # Calculate average cheap price
        avg_cheap = sum(f.price for f in cheap_foods) / len(cheap_foods) if cheap_foods else 0
        info += f"📊 **Affordable Range:** {format_price_kwacha(min(f.price for f in cheap_foods))} - {format_price_kwacha(max(f.price for f in cheap_foods))}\n"
        info += f"📈 **Average Affordable Price:** {format_price_kwacha(avg_cheap)}\n"
        
        return info
    except Exception as e:
        logger.error(f"Error fetching cheap food: {e}")
        return "Unable to fetch affordable options at the moment."


def get_user_breakdown_formatted():
    """Get user statistics"""
    try:
        total_users = User.objects.count()
        customers = User.objects.filter(user_type='customer').count()
        staff = User.objects.filter(user_type='staff').count()
        admins = User.objects.filter(user_type='admin').count()
        
        info = "👥 **📊 Community Statistics**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        info += f"• **Total Community Members:** {total_users}\n"
        info += f"• **Customers:** {customers}\n"
        info += f"• **Restaurant Staff:** {staff}\n"
        info += f"• **Administrators:** {admins}\n"
        
        return info
    except Exception as e:
        logger.error(f"Error fetching user breakdown: {e}")
        return "Community statistics unavailable."


# ========= QUERY ANALYSIS ========= #
def analyze_query(user_query, history):
    """Analyze user query to determine response type"""
    query = user_query.lower()
    
    # Check for database queries (factual)
    if any(word in query for word in ['all food', 'list food', 'menu', 'what food', 'show food']):
        return "food_list"
    
    elif any(word in query for word in ['cheap', 'affordable', 'budget', 'low price', 'inexpensive']):
        return "cheap_food"
    
    elif any(word in query for word in ['recommend', 'suggestion', 'what should', 'best', 'popular']):
        return "recommendations"
    
    elif any(word in query for word in ['k50', 'k100', 'k200', 'budget of', 'have k']):
        # Extract budget amount
        import re
        budget_match = re.search(r'k(\d+)', query)
        if budget_match:
            return f"budget_{budget_match.group(1)}"
        return "budget_general"
    
    elif any(word in query for word in ['user', 'customer', 'people', 'community', 'members']):
        return "users"
    
    elif any(word in query for word in ['about', 'what is', 'platform', 'system', 'purpose']):
        return "platform_info"
    
    elif any(word in query for word in ['help', 'how to', 'guide', 'what can i ask']):
        return "help"
    
    # Check for follow-ups
    elif query in ['yes', 'sure', 'ok', 'please', 'go ahead', 'more']:
        if history:
            for msg in reversed(history):
                if msg.get("type") == "user":
                    last_query = msg.get("content", "").lower()
                    if "food" in last_query:
                        return "food_list"
                    elif "budget" in last_query or "k" in last_query:
                        return "budget_general"
        
        return "help"  # Default to help
    
    # Default to general conversation
    else:
        return "general"


def get_db_data(query_type, user_query=""):
    """Get database data or prepare context based on query type"""
    if query_type == "food_list":
        return get_all_food_items_formatted()
    elif query_type == "cheap_food":
        return get_cheap_food_options()
    elif query_type == "recommendations":
        return get_food_recommendations()
    elif query_type.startswith("budget_"):
        try:
            budget = int(query_type.split("_")[1])
            return get_food_for_budget(budget)
        except:
            return "Please specify a budget amount (e.g., 'K50', 'K100')"
    elif query_type == "users":
        return get_user_breakdown_formatted()
    elif query_type == "platform_info":
        return get_platform_info()
    elif query_type == "help":
        return get_help_info()
    else:
        return "general_context"


def get_help_info():
    """Get help information about what users can ask"""
    info = """🤖 **💡 What You Can Ask Me:**

**🍽️ Food & Menu:**
• "Show me all food" - See complete menu
• "What's cheap?" - Affordable options
• "Recommendations" - Popular picks
• "Traditional food" - Zambian dishes
• "What can I get for K100?" - Budget options

**🏪 Platform Info:**
• "What is EatNearBY?" - Learn about us
• "How does it work?" - Platform guide
• "Who can use it?" - User types

**👥 Community:**
• "How many users?" - Community stats
• "Tell me about customers" - User information

**💰 Budget Help:**
• "I have K50" - Options within budget
• "Cheap food under K30" - Specific budget
• "Best value meals" - Good deals

**🎯 General Questions:**
• "Hello" / "Hi" - Greet me
• "Help" - See this menu again
• "Thank you" - Polite responses
• "How are you?" - Casual chat

**💬 Examples:**
• "What's the most popular food?"
• "Show me Zambian dishes"
• "I want something traditional"
• "What's good for lunch?"
• "Any special deals?"

💡 **Tip:** I can understand natural language! Just ask like you're talking to a friend."""
    
    return info


# ========= OPENROUTER QUERY ========= #
def query_openrouter(prompt: str, context: str = "", query_type: str = "general") -> str:
    """
    Send a prompt to OpenRouter API with balanced instructions.
    """
    for attempt in range(RETRY_LIMIT):
        api_key = get_current_api_key()
        
        if not api_key:
            logger.error("No API keys available")
            return "Error: No API keys configured. Please contact administrator."
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://eatnearby.com",
            "X-Title": "EatNearBY Assistant"
        }
        
        # Balanced system prompt
        system_content = f"""You are EatNearBY Assistant, a friendly and helpful chatbot for the EatNearBY food community platform in Zambia.

**ABOUT EATNEARBY:**
EatNearBY connects restaurants near Evelyn Hone College with customers through online food ordering, restaurant discovery, and community engagement.

**YOUR ROLE:**
1. **For database queries:** Use the exact data provided below
2. **For general questions:** Be creative, helpful, and friendly
3. **For budget queries:** Suggest realistic options based on available data
4. **Always:** Be warm, engaging, and customer-focused

**DATABASE CONTEXT:**
{context}

**USER QUERY:** {prompt}

**RESPONSE GUIDELINES:**
1. **Be conversational and friendly** - Use emojis naturally
2. **For factual queries:** Stick to the database data
3. **For general questions:** Be helpful and creative
4. **For budget questions:** Suggest combos and options
5. **Always mention prices in Zambian Kwacha (K)**
6. **Never invent fake products** - if data is missing, suggest alternatives
7. **Make users feel welcome** - this is a food community!

**EXAMPLES:**
User: "What can I get for K100?"
You: "With K100, you could get [real item 1] + [real item 2]! Or try [real item 3] which is very popular. Would you like me to suggest some combos?"

User: "Recommend something good"
You: "Based on our menu, I'd recommend [real popular item]. It's [description]. Or if you prefer traditional Zambian food, try [real traditional item]!"

**REMEMBER:** You're helping real people enjoy good food!"""
        
        # Adjust temperature based on query type
        temperature = 0.3 if query_type in ["general", "recommendations", "budget_general"] else 0.1
        
        payload = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "temperature": temperature,
            "top_p": 0.8,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            logger.info(f"Querying OpenRouter (attempt {attempt + 1})")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                response_text = data["choices"][0]["message"]["content"]
                
                # Ensure Kwacha formatting
                if "$" in response_text:
                    response_text = response_text.replace("$", "K")
                
                return response_text
            else:
                logger.warning(f"Unexpected response format: {data}")
                return "I'd love to help! Could you try asking in a different way?"
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            logger.error(f"HTTP error {status_code}: {e}")
            
            if status_code == 429 or "quota" in str(e).lower():
                logger.warning("⚠️ Rate limit/quota exceeded — rotating key")
                rotate_api_key()
                if attempt < RETRY_LIMIT - 1:
                    import time
                    time.sleep(2)
                    continue
            
            return "The service is having a quick break. Please try again in a moment!"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < RETRY_LIMIT - 1:
                import time
                time.sleep(1)
                continue
            return "I'm having trouble connecting right now. Please check your internet connection."
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Oops! Something went wrong: {str(e)}"
    
    return "I'm taking a quick break. Please try again in a moment!"


# ========= MAIN ENTRY ========= #
def get_gemini_response(user_prompt: str, user_type: str = 'guest') -> str:
    """
    Main entry function - balanced approach for factual and creative responses.
    """
    try:
        # Load chat history
        history = load_chat_history()
        
        # Analyze the query
        query_type = analyze_query(user_prompt, history)
        
        # Get database context
        db_context = get_db_data(query_type, user_prompt)
        
        # Build user context
        user_context_map = {
            'admin': "User is an ADMINISTRATOR with full system access.",
            'staff': "User is RESTAURANT STAFF who manages a restaurant.",
            'customer': "User is a CUSTOMER looking for food options.",
            'guest': "User is a GUEST exploring the platform."
        }
        user_context = user_context_map.get(user_type, user_context_map['guest'])
        
        # Prepare final context
        if db_context == "general_context":
            final_context = f"{user_context}\n\nEatNearBY is a food community platform in Zambia. We have various food items available. All prices are in Zambian Kwacha (K)."
        else:
            final_context = f"{user_context}\n\nDATABASE CONTEXT:\n{db_context}"
        
        # Get response from OpenRouter
        answer = query_openrouter(user_prompt, final_context, query_type)
        
        # Save to chat history
        history.append({
            "type": "user", 
            "content": user_prompt, 
            "time": datetime.now().isoformat(),
            "user_type": user_type
        })
        history.append({
            "type": "assistant", 
            "content": answer, 
            "time": datetime.now().isoformat(),
            "query_type": query_type
        })
        save_chat_history(history)
        
        logger.info(f"✅ Chatbot: Query='{user_prompt[:30]}...', Type='{query_type}', User='{user_type}'")
        
        return answer
        
    except Exception as e:
        logger.error(f"❌ Chatbot error: {e}", exc_info=True)
        return "I'm having a bit of trouble right now. Please try again in a moment or contact support if it continues. 😊"