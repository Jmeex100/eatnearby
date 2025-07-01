

from django.db import models
from django.contrib.auth.models import AbstractUser
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} in {self.challenge.title}"

    class Meta:
        unique_together = ('challenge', 'user', 'post')

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
# ✅ Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# ✅ Abstract Product Model
class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)  
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=300, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='%(class)s_products')  # Dynamic related_name
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (${self.price})"


# ✅ FastFood Model (inherits from Product)
class FastFood(Product):
    class Meta:
        verbose_name = "Fast Food"
        verbose_name_plural = "Fast Foods"


# ✅ Food Model (inherits from Product)
class Food(Product):
    class Meta:
        verbose_name = "Food"
        verbose_name_plural = "Foods"


# ✅ Drink Model (inherits from Product)
class Drink(Product):
    class Meta:
        verbose_name = "Drink"
        verbose_name_plural = "Drinks"

# ✅ Custom User Model
class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('staff', 'Staff'),
    ]
    GENDER_TYPE_CHOICES = [
    ('mr', 'Mr.'),
    ('mrs', 'Mrs.'),
    ('miss', 'Miss'),
    ('ms', 'Ms.'),
    ]


    def user_directory_path(instance, filename):
        # File will be uploaded to MEDIA_ROOT/profile_images/<username>/<filename>
        return f'profile_images/{instance.username}/{filename}'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    gender = models.CharField(max_length=10, choices=GENDER_TYPE_CHOICES, blank=True, null=True)
    phone_number = models.IntegerField(blank=True, null=True)
    email = models.EmailField(max_length=100,unique=True, blank=False, null=True)
    image = models.ImageField(
        upload_to=user_directory_path,
        default='auths/images/empty.png',
        blank=True,
        null=True,
        verbose_name="Profile Image"
    )

    def __str__(self):
        gender_prefix = dict(self.GENDER_TYPE_CHOICES).get(self.gender, "")
        return f"{gender_prefix} {self.first_name} {self.last_name} ({self.get_user_type_display()})"
  # payments/models.py
from django.db import models
from auths.models import User
from cart.models import Cart
import logging

logger = logging.getLogger(__name__)

class DeliveryInfo(models.Model):
    id = models.BigAutoField(primary_key=True)

    DELIVERY_POINTS = [
        ('evelyhone', 'Evelyn Hone College'),
        ('zambia_police', 'Zambia Police Headquarters'),
        ('zambia_accountancy', 'Zambia Centre for Accountancy'),
        ('mukuba_house', 'Mukuba Pension House'),
        ('bus_terminus', 'Lusaka Intercity Bus Terminus'),
        ('national_museum', 'Lusaka National Museum'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Card'),
    ]

    MOBILE_MONEY_PROVIDERS = [
        ('airtel', 'Airtel'),
        ('mtn', 'MTN'),
        ('zamtel', 'Zamtel'),
    ]

    CARD_PROVIDERS = [
        ('paypal', 'Paypal'),
        ('pesapal', 'Pesapal'),
        ('stripe', 'Stripe'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, blank=True, null=True)
    predefined_address = models.CharField(
        max_length=30,
        choices=DELIVERY_POINTS,
        blank=True,
        null=True,
        help_text="Predefined delivery point"
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending',
        help_text="Current delivery status"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash',
        help_text="Payment method used"
    )
    payment_provider = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Specific provider for Mobile Money or Card (e.g., Airtel, Stripe)"
    )
    phone_number = models.CharField(max_length=20)
    secondary_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Optional secondary contact number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = DeliveryInfo.objects.get(pk=self.pk)
                if old_instance.delivery_status != self.delivery_status:
                    logger.info(
                        f"DeliveryInfo {self.id} status changed from "
                        f"{old_instance.delivery_status} to {self.delivery_status}"
                    )
            except DeliveryInfo.DoesNotExist:
                logger.warning(f"DeliveryInfo {self.id} not found during save")
        else:
            logger.info(f"New DeliveryInfo created with status {self.delivery_status}")
        if self.predefined_address and not self.address:
            self.address = self.get_predefined_address_display()
        super().save(*args, **kwargs)

    def __str__(self):
        address_display = self.address or self.get_predefined_address_display() or "N/A"
        return f"Delivery for {self.user.username} at {address_display}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Info"
        verbose_name_plural = "Delivery Info"


class PaymentHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # paypal transaction
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    delivery_info = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_histories'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    items = models.JSONField(
        help_text="List of items in the payment (e.g., [{'name': 'Pizza', 'quantity': 2, 'subtotal': 15.00}])"
    )

    def __str__(self):
        return f"Payment by {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment History"
        verbose_name_plural = "Payment Histories"   from django.db import models
from auths.models import User
from payments.models import DeliveryInfo

class StaffServiceArea(models.Model):
    """
    Maps staff members to the predefined delivery points they can serve.
    """
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='service_areas'
    )
    point = models.CharField(
        max_length=30,
        choices=DeliveryInfo.DELIVERY_POINTS,
        help_text="Which delivery point this staff covers"
    )

    class Meta:
        unique_together = ('staff', 'point')
        verbose_name = "Staff Service Area"
        verbose_name_plural = "Staff Service Areas"

    def __str__(self):
        return f"{self.staff.username} covers {self.get_point_display()}"

class StaffAssignment(models.Model):
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='delivery_assignments'
    )
    delivery = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['staff', 'delivery']
        verbose_name = "Staff Assignment"
        verbose_name_plural = "Staff Assignments"

    def __str__(self):
        return f"{self.staff.username} assigned to Delivery {self.delivery.id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('delivery_almost_complete', 'Delivery Almost Complete'),
        ('delivery_completed', 'Delivery Completed'),
        ('alert', 'Alert'),
        ('delivery_declined', 'Delivery Declined'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='notifications'
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='new_order'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_delivery = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"