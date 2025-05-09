# C:\Users\Surecode\Documents\GitHub\django\coreEat\auths\models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

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
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=False, null=True)
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
 