from django.db.models import Q
import random
import logging

logger = logging.getLogger(__name__)

# Greeting responses
GREETINGS = [
    "Hello there! How can I help you today?",
    "Hi! What can I do for you?",
    "Hey! Nice to see you. What's on your mind?",
    "Greetings! How may I assist you?",
    "Hello! Ready to explore EatNear BY?"
]

# Farewell responses
FAREWELLS = [
    "Goodbye! Come back anytime.",
    "See you later!",
    "Have a great day!",
    "Bye! Don't hesitate to return if you have more questions.",
    "Until next time!"
]

# Small talk responses
SMALL_TALK = {
    "how are you": ["I'm doing great, thanks for asking!", "Just fine! How about you?", "All systems operational!"],
    "what's up": ["Not much, just here to help!", "The usual - helping users like you!", "Everything's good!"],
    "thank you": ["You're welcome!", "Happy to help!", "Anytime!"],
    "thanks": ["My pleasure!", "No problem at all!", "Glad I could assist!"],
    "you're awesome": ["Aw, thanks! You're pretty great yourself!", "That's so nice of you to say!", "I try my best!"]
}

def get_admin_responses(message, restaurants, recipes, challenges):
    """Handle admin-specific queries"""
    message = message.lower()
    logger.info(f"Processing admin query: {message}")
    
    if any(word in message for word in ['manage', 'admin', 'control', 'moderate']):
        if 'restaurant' in message:
            count = restaurants.count()
            return f"You can manage {count} restaurants:\n1. Add new restaurants\n2. Edit existing ones\n3. Remove restaurants\n4. Verify restaurant information"
        
        if 'challenge' in message:
            active = challenges.count()
            return f"Manage {active} active challenges:\n1. Create new challenges\n2. Edit current ones\n3. End challenges\n4. View participation stats"
        
        if 'content' in message or 'post' in message:
            return "Content moderation options:\n1. Review flagged content\n2. Remove inappropriate posts\n3. Ban users\n4. View moderation logs"
        
        if 'user' in message:
            return "User management:\n1. View all users\n2. Edit user permissions\n3. Ban/suspend users\n4. View user activity"
    
    if any(word in message for word in ['system', 'stats', 'report', 'analytics']):
        return ("System reports available:\n"
                "- Restaurant statistics\n"
                "- User engagement metrics\n"
                "- Challenge participation\n"
                "- Revenue reports\n"
                "- System health status")
    
    if 'help' in message:
        return get_help_response('admin')
    
    return None

def get_staff_responses(message, restaurants, recipes, challenges):
    """Handle staff-specific queries"""
    message = message.lower()
    logger.info(f"Processing staff query: {message}")
    
    if any(word in message for word in ['restaurant', 'menu', 'profile', 'hours']):
        return ("Restaurant management options:\n"
                "1. Update profile information\n"
                "2. Edit menu items\n"
                "3. Set operating hours\n"
                "4. Upload photos\n"
                "5. View customer reviews")
    
    if any(word in message for word in ['customer', 'question', 'answer', 'respond']):
        return ("Customer interaction:\n"
                "1. View unanswered questions\n"
                "2. Respond to customer queries\n"
                "3. Manage reviews\n"
                "4. Create special offers")
    
    if any(word in message for word in ['order', 'reservation', 'booking']):
        return ("Order/reservation management:\n"
                "1. View today's reservations\n"
                "2. Check order status\n"
                "3. Update order details\n"
                "4. Manage waitlist")
    
    if 'help' in message:
        return get_help_response('staff')
    
    return None

def get_recipe_details(recipe):
    """Generate detailed information about a recipe"""
    ingredients = [f"{ing.quantity} {ing.name} {ing.notes or ''}".strip() for ing in recipe.ingredients.all()]
    instructions = [f"{ins.step_number}. {ins.instruction}" for ins in recipe.instructions.all()]
    tags = [tag.name for tag in recipe.tags.all()]
    
    ingredients_text = "\n- ".join(ingredients) if ingredients else "Not specified"
    instructions_text = "\n".join(instructions) if instructions else "Not specified"
    
    details = [
        f"📝 {recipe.title}",
        f"⏱️ Prep: {recipe.prep_time} mins | Cook: {recipe.cook_time} mins",
        f"🍽️ Serves: {recipe.servings}",
        f"📊 Difficulty: {recipe.get_difficulty_display()}",
        f"🥗 Ingredients:\n- {ingredients_text}",
        f"📝 Instructions:\n{instructions_text}",
        f"🏷️ Tags: {', '.join(tags) if tags else 'None'}"
    ]
    if recipe.image:
        details.append(f"🖼️ Image: {recipe.image.url}")
    
    return "\n".join(details)

def get_common_responses(message, restaurants, recipes, challenges):
    """Handle common queries for all user types"""
    message = message.lower().strip()
    logger.info(f"Processing common query: {message}")
    
    # Greetings
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        return random.choice(GREETINGS)
    
    # Farewells
    if any(word in message for word in ['bye', 'goodbye', 'see you', 'later']):
        return random.choice(FAREWELLS)
    
    # Small talk
    for phrase, responses in SMALL_TALK.items():
        if phrase in message:
            return random.choice(responses)
    
    # Restaurant queries
    if any(word in message for word in ['restaurant', 'eat', 'dine', 'food place', 'hungry']) or message in [r.name.lower() for r in restaurants]:
        if not restaurants.exists():
            return "We don't have any restaurants listed yet. Check back soon!"
        
        # Specific restaurant name match
        restaurant = restaurants.filter(name__icontains=message).first()
        if restaurant:
            details = [
                f"🍽️ {restaurant.name}",
                f"📍 Address: {restaurant.address}, {restaurant.city}, {restaurant.country}",
                f"📧 Email: {restaurant.email or 'Not provided'}",
                f"📞 Phone: {restaurant.phone or 'Not provided'}",
                f"🌐 Website: {restaurant.website or 'Not provided'}",
                f"📝 Description: {restaurant.description or 'No description available'}",
                f"✅ Verified: {'Yes' if restaurant.is_verified else 'No'}"
            ]
            if restaurant.profile_image:
                details.append(f"🖼️ Image: {restaurant.profile_image.url}")
            return "\n".join(details)
        
        if 'near me' in message:
            return "I can show you restaurants near your location. Please enable location services."
        
        if 'recommend' in message or 'suggest' in message:
            featured = restaurants.order_by('?').first()
            return f"I recommend trying {featured.name}! Located at {featured.address}, {featured.city}."
        
        if 'vegetarian' in message or 'vegan' in message:
            veg_restaurants = [r.name for r in restaurants.filter(has_vegetarian=True)]
            if veg_restaurants:
                return f"Vegetarian-friendly options: {', '.join(veg_restaurants)}"
            return "We don't have specific vegetarian listings yet."
        
        names = [r.name for r in restaurants]
        return f"We have these restaurants: {', '.join(names)}. Try typing a name like 'happy customers' for details."
    
    # Recipe queries
    if any(word in message for word in ['recipe', 'cook', 'make', 'prepare', 'dish', 'samp', 'vitumbuwa', 'sweet rice']):
        if not recipes.exists():
            return "Our recipe collection is empty right now. Check back later!"
        
        # Specific recipe match
        recipe = recipes.filter(Q(title__icontains=message) | Q(tags__name__icontains=message)).first()
        if recipe:
            return get_recipe_details(recipe)
        
        if 'easy' in message:
            easy_recipes = [r.title for r in recipes.filter(difficulty='EASY')]
            return f"Easy recipes: {', '.join(easy_recipes[:3] if easy_recipes else ['None available'])}"
        
        if 'quick' in message or 'fast' in message:
            quick_recipes = [r.title for r in recipes.filter(prep_time__lte=15)]
            return f"Quick recipes (≤15 min prep): {', '.join(quick_recipes[:3] if quick_recipes else ['None available'])}"
        
        if 'african' in message:
            african_recipes = [r.title for r in recipes.filter(tags__name__iexact='african')]
            return f"African recipes: {', '.join(african_recipes[:3] if african_recipes else ['None available'])}"
        
        names = [r.title for r in recipes]
        return f"Available recipes: {', '.join(names[:5])}. Try typing a recipe name like 'African Samp' for details."
    
    # Challenge queries
    if any(word in message for word in ['challenge', 'compete', 'participate', 'contest']):
        if not challenges.exists():
            return "No active challenges at the moment. Check back soon!"
        
        if 'join' in message or 'participate' in message:
            return "You can join any active challenge from the Challenges page. Would you like me to list them?"
        
        if 'win' in message or 'prize' in message:
            return "Current challenge prizes include discounts, free meals, and special badges!"
        
        names = [c.title for c in challenges]
        return f"Active challenges: {', '.join(names)}. Want to know more about any?"
    
    # Detailed information requests
    if 'tell me about' in message or 'info about' in message or 'details about' in message:
        name = message.split('about')[-1].strip().lower()
        
        # Restaurant details
        restaurant = restaurants.filter(name__icontains=name).first()
        if restaurant:
            details = [
                f"🍽️ {restaurant.name}",
                f"📍 Address: {restaurant.address}, {restaurant.city}, {restaurant.country}",
                f"📧 Email: {restaurant.email or 'Not provided'}",
                f"📞 Phone: {restaurant.phone or 'Not provided'}",
                f"🌐 Website: {restaurant.website or 'Not provided'}",
                f"📝 Description: {restaurant.description or 'No description available'}",
                f"✅ Verified: {'Yes' if restaurant.is_verified else 'No'}"
            ]
            if restaurant.profile_image:
                details.append(f"🖼️ Image: {restaurant.profile_image.url}")
            return "\n".join(details)
        
        # Recipe details
        recipe = recipes.filter(Q(title__icontains=name) | Q(tags__name__icontains=name)).first()
        if recipe:
            return get_recipe_details(recipe)
        
        # Challenge details
        challenge = challenges.filter(title__icontains=name).first()
        if challenge:
            details = [
                f"🏆 {challenge.title}",
                f"📅 Runs from {challenge.start_date} to {challenge.end_date}",
                f"📝 {challenge.description}",
                f"👥 Participants: {challenge.participants.count()}",
                f"🔹 Status: {'Active' if challenge.is_active else 'Ended'}"
            ]
            return "\n".join(details)
        
        return f"I couldn't find anything matching '{name}'. Try asking about restaurants, recipes, or challenges."
    
    # Fallback responses
    fallbacks = [
        "I'm not sure I understand. Try typing a restaurant name like 'happy customers' or ask about recipes or challenges.",
        "Could you clarify? I can help with restaurant details, recipe ideas, or challenges!",
        "Not sure what you mean. Want to explore restaurants like 'Shi Bupe's Matebeto Restaurant'?",
        "I can assist with restaurants, recipes, or challenges. Try 'happy customers' or 'African Samp recipe'.",
        "Hmm, let's try that again. Ask about a specific restaurant, recipe, or challenge!"
    ]
    return random.choice(fallbacks)

def get_help_response(user_type):
    """Return expanded help message based on user type"""
    if user_type == 'admin':
        return ("🛠️ Admin Help Center 🛠️\n\n"
                "Restaurant Management:\n"
                "- Add/Edit/Remove restaurants\n"
                "- Verify restaurant information\n"
                "- View restaurant analytics\n\n"
                "Challenge Management:\n"
                "- Create new challenges\n"
                "- Monitor participation\n"
                "- Adjust challenge parameters\n\n"
                "Content Moderation:\n"
                "- Review flagged content\n"
                "- Manage user reports\n"
                "- Ban/suspend users\n\n"
                "System Tools:\n"
                "- View system health\n"
                "- Generate reports\n"
                "- Configure settings")
    
    elif user_type == 'staff':
        return ("👨‍🍳 Staff Help Center 👩‍🍳\n\n"
                "Restaurant Profile:\n"
                "- Update business info\n"
                "- Manage menu items\n"
                "- Set operating hours\n\n"
                "Customer Interaction:\n"
                "- Answer questions\n"
                "- Respond to reviews\n"
                "- Create promotions\n\n"
                "Order Management:\n"
                "- View reservations\n"
                "- Process orders\n"
                "- Manage waitlist\n\n"
                "Performance:\n"
                "- View customer feedback\n"
                "- Check ratings\n"
                "- See popular items")
    
    else:
        return ("🤗 Customer Help Center 🤗\n\n"
                "Discover Restaurants:\n"
                "- Find nearby places\n"
                "- Filter by cuisine\n"
                "- Read reviews\n\n"
                "Explore Recipes:\n"
                "- Browse by difficulty\n"
                "- Search by ingredients\n"
                "- Save favorites\n\n"
                "Join Challenges:\n"
                "- See active challenges\n"
                "- Track progress\n"
                "- Claim rewards\n\n"
                "Community Features:\n"
                "- Ask questions\n"
                "- Share experiences\n"
                "- Connect with foodies")