from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

User = settings.AUTH_USER_MODEL

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# ✅ Restaurant (3NF compliant - all attributes depend on PK)
class Restaurant(TimestampMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='Restaurant/', blank=True, null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Zambia')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['city', 'country']),
        ]

# ✅ User Profile Extension (1:1 with auth User)
class UserProfile(TimestampMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    dietary_preferences = models.CharField(max_length=255, blank=True)
    favorite_restaurants = models.ManyToManyField(Restaurant, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"

# ✅ Content Base Model (Abstract)
class ContentBase(TimestampMixin):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

# ✅ Post (General community content)
class Post(ContentBase):
    POST_TYPES = [
        ('STORY', 'Story'),
        ('TIP', 'Tip'),
        ('QUESTION', 'Question'),
        ('REVIEW', 'Review'),
    ]
    
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='STORY')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    likes = models.ManyToManyField(User, through='PostLike', related_name='liked_posts')
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post_type']),
            models.Index(fields=['restaurant']),
        ]

# ✅ Post Like (Junction table for many-to-many)
class PostLike(TimestampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'post')

# ✅ Review (Specialized Post with rating)
class Review(TimestampMixin):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    food_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    service_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    ambiance_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    def __str__(self):
        return f"Review {self.rating}★ for {self.post.restaurant}"

# ✅ Comment (For posts and other comments)
class Comment(TimestampMixin):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    likes = models.ManyToManyField(User, through='CommentLike', related_name='liked_comments')
    
    def __str__(self):
        return f"Comment by {self.author.username}"

    class Meta:
        ordering = ['created_at']

# ✅ Comment Like (Junction table)
class CommentLike(TimestampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'comment')

# ✅ Challenge
class Challenge(TimestampMixin):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    banner_image = models.ImageField(upload_to='challenges/', blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    participants = models.ManyToManyField(User, through='ChallengeParticipation', related_name='challenges')
    
    def __str__(self):
        return self.title

# ✅ Challenge Participation
class ChallengeParticipation(TimestampMixin):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} in {self.challenge.title}"

    class Meta:
        unique_together = ('challenge', 'user')  

# ✅ Recipe
class Recipe(ContentBase):
    prep_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    cook_time = models.PositiveIntegerField(help_text="Cooking time in minutes")
    servings = models.PositiveSmallIntegerField()
    difficulty = models.CharField(max_length=20, choices=[
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard')
    ])
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    tags = models.ManyToManyField('RecipeTag', related_name='recipes')
    
    def __str__(self):
        return self.title

# ✅ Recipe Ingredient (Separate model for normalization)
class RecipeIngredient(TimestampMixin):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)
    notes = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.quantity} {self.name}"

# ✅ Recipe Instruction (Separate model for normalization)
class RecipeInstruction(TimestampMixin):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='instructions')
    step_number = models.PositiveSmallIntegerField()
    instruction = models.TextField()
    
    def __str__(self):
        return f"Step {self.step_number} for {self.recipe.title}"

    class Meta:
        ordering = ['step_number']
        unique_together = ('recipe', 'step_number')

# ✅ Recipe Tag (For categorization)
class RecipeTag(TimestampMixin):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

# ✅ Q&A with Restaurants
class RestaurantQuestion(TimestampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    question = models.TextField()
    is_answered = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Question from {self.user.username} to {self.restaurant.name}"

    class Meta:
        ordering = ['-created_at']

# ✅ Q&A Answer
class RestaurantAnswer(TimestampMixin):
    question = models.OneToOneField(RestaurantQuestion, on_delete=models.CASCADE, related_name='answer')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.TextField()
    
    def __str__(self):
        return f"Answer to {self.question}"