<!-- food -->
https://lowcarbafrica.com/banga-soup-palm-nut-soup/
https://zambiankitchen.com/samoosa-recipe/#google_vignette




 i  have those app 
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sim',
    'auths',
hey lets add a fix cart for a django app rom django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sim.urls')),
    path('', include('auths.urls')),
    path('cart', include('cart.urls')),
    
   
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# C:\Users\Surecode\Documents\GitHub\django\coreEat\cart\models.py
# Create your models here.
from django.db import models
from auths.models import User, FastFood, Food, Drink

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        return sum(item.subtotal() for item in self.cartitem_set.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    fast_food = models.ForeignKey(FastFood, null=True, blank=True, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, null=True, blank=True, on_delete=models.CASCADE)
    drink = models.ForeignKey(Drink, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
   
    

    def get_product(self):
        return self.fast_food or self.food or self.drink

    def subtotal(self):
        product = self.get_product()
        if not product:
            return 0
        base_price = product.price
        quality_multipliers = {
            'standard': 1.0,
            'premium': 1.2,
            'deluxe': 1.5
        }
        return base_price * self.quantity * quality_multipliers[self.quality]

    def __str__(self):
        product = self.get_product()
        return f"{product.name} x{self.quantity} ({self.quality})"  no need for quality please remove it   from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_view, name='cart_view'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/', views.update_cart, name='update_cart'),
]  # cart/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from auths.models import FastFood, Food, Drink
from .models import Cart, CartItem
import json

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        # Handle both AJAX and form submission
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            quality = data.get('quality', 'standard')
        else:
            product_id = request.POST.get('product_id') or request.path.split('/')[-2]
            quantity = int(request.POST.get('quantity', 1))
            quality = request.POST.get('quality', 'standard')

        # Find the product
        product = None
        for model in [FastFood, Food, Drink]:
            try:
                product = model.objects.get(product_id=product_id)
                break
            except model.DoesNotExist:
                continue
        
        if not product:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Product not found'})
            messages.error(request, 'Product not found')
            return redirect('auths:orders')

        # Map model name to CartItem field name
        model_name = product.__class__.__name__.lower()
        field_name = 'fast_food' if model_name == 'fastfood' else model_name

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            **{field_name: product},
            defaults={'quantity': quantity, 'quality': quality}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.quality = quality
            cart_item.save()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'cart_count': cart.cartitem_set.count(),
                'cart_total': float(cart.total())
            })
        
        messages.success(request, 'Item added to your cart!')
        return redirect('cart:cart_view')
    
    return redirect('auths:orders')

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    
    context = {
        'cart_items': cart_items,
        'total': cart.total()
    }
    return render(request, 'cart/cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart:cart_view')

@login_required
def update_cart(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 0))
        quality = data.get('quality', 'standard')

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.quality = quality
            cart_item.save()

        return JsonResponse({
            'success': True,
            'subtotal': float(cart_item.subtotal()),
            'cart_total': float(cart.total()),
            'cart_count': cart.cartitem_set.count()
        })
    return JsonResponse({'success': False, 'error': 'Invalid request'})  {% extends 'base.html' %}
{% block title %}Your Cart{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">Your Shopping Cart</h1>
    
    <div class="bg-white shadow-md rounded-lg p-6">
        {% for item in cart_items %}
        <div class="cart-item flex items-center justify-between py-4 border-b" data-item-id="{{ item.id }}">
            <div class="flex items-center">
                <img src="{{ item.get_product.image_url }}" alt="{{ item.get_product.name }}" class="w-16 h-16 object-cover mr-4">
                <div>
                    <h3 class="text-lg font-semibold">{{ item.get_product.name }}</h3>
                    <p class="text-gray-600">Quality: 
                        <select class="quality-select border rounded p-1">
                            <option value="standard" {% if item.quality == 'standard' %}selected{% endif %}>Standard</option>
                            <option value="premium" {% if item.quality == 'premium' %}selected{% endif %}>Premium</option>
                            <option value="deluxe" {% if item.quality == 'deluxe' %}selected{% endif %}>Deluxe</option>
                        </select>
                    </p>
                </div>
            </div>
            <div class="flex items-center">
                <input type="number" class="quantity w-16 border rounded p-1 mr-4" value="{{ item.quantity }}" min="0">
                <span class="subtotal mr-4">K{{ item.subtotal|floatformat:2 }}</span>
                <button class="update-btn bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-500">Update</button>
            </div>
        </div>
        {% empty %}
        <p class="text-gray-600">Your cart is empty</p>
        {% endfor %}
        
        {% if cart_items %}
        <div class="mt-6 text-right">
            <p class="text-xl font-bold">Total: K<span id="cart-total">{{ total|floatformat:2 }}</span></p>
        </div>
        {% endif %}
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
    $('.update-btn').click(function() {
        const $item = $(this).closest('.cart-item');
        const itemId = $item.data('item-id');
        const quantity = $item.find('.quantity').val();
        const quality = $item.find('.quality-select').val();

        $.ajax({
            url: '{% url "cart:update_cart" %}',  // Note: You need to add this view and URL
            method: 'POST',
            data: JSON.stringify({
                item_id: itemId,
                quantity: quantity,
                quality: quality
            }),
            contentType: 'application/json',
            headers: {'X-CSRFToken': '{{ csrf_token }}'},
            success: function(response) {
                if (response.success) {
                    if (quantity <= 0) {
                        $item.remove();
                    } else {
                        $item.find('.subtotal').text('K' + response.subtotal.toFixed(2));
                    }
                    $('#cart-total').text(response.cart_total.toFixed(2));
                    if (response.cart_count === 0) {
                        $('.bg-white').html('<p class="text-gray-600">Your cart is empty</p>');
                    }
                }
            }
        });
    });
});
</script>
{% endblock %}   cart\templates\cart\cart.html   in my main # C:\Users\Surecode\Documents\GitHub\django\coreEat\auths\models.py

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


# ✅ Custom User Model (inherits from AbstractUser)
class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('staff', 'Staff'),
    ]

    GENDER_TYPE_CHOICES = [
        ('male', 'Mr.'),
        ('female', 'Mrs.'),
        ('other', 'Other'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    gender = models.CharField(max_length=10, choices=GENDER_TYPE_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        gender_prefix = dict(self.GENDER_TYPE_CHOICES).get(self.gender, "")
        return f"{gender_prefix} {self.first_name} {self.last_name} ({self.get_user_type_display()})" dont change work with that  # auths/urls.py
from django.urls import path
from .views import auth_views, product_views, profile_views, misc_views

urlpatterns = [
    # Auth
    path('login/', auth_views.login_page, name='login'),
    path('register/', auth_views.register_page, name='register'),
    path('logout/', auth_views.logout_page, name='logout'),

    # Products
    path('orders/', product_views.orders, name='orders'),
    path('order/<str:item_id>/<str:category>/', product_views.order, name='order'),
    path('products/', product_views.products, name='products'),

    # Profile
    path('profile/', profile_views.profile, name='profile'),
    path('settings/', profile_views.settings, name='settings'),

    # Misc
    path('index', misc_views.index, name='index'),
    path('help/', misc_views.help_page, name='help'),
]    from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from ..models import FastFood, Food, Drink, Category
# C:\Users\Surecode\Documents\GitHub\django\coreEat\auths\views\product_views.py
def orders(request):
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category_id = request.GET.get('category')
    sort = request.GET.get('sort')

    # Base querysets
    fast_foods = FastFood.objects.all()
    foods = Food.objects.all()
    drinks = Drink.objects.all()

    # Apply search query
    if query:
        fast_foods = fast_foods.filter(Q(name__icontains=query) | Q(description__icontains=query))
        foods = foods.filter(Q(name__icontains=query) | Q(description__icontains=query))
        drinks = drinks.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Apply price range filtering
    if min_price:
        fast_foods = fast_foods.filter(price__gte=min_price)
        foods = foods.filter(price__gte=min_price)
        drinks = drinks.filter(price__gte=min_price)
    if max_price:
        fast_foods = fast_foods.filter(price__lte=max_price)
        foods = foods.filter(price__lte=max_price)
        drinks = drinks.filter(price__lte=max_price)

    # Apply category filtering
    if category_id:
        fast_foods = fast_foods.filter(category_id=category_id)
        foods = foods.filter(category_id=category_id)
        drinks = drinks.filter(category_id=category_id)

    # Apply sorting
    if sort == 'price_asc':
        fast_foods = fast_foods.order_by('price')
        foods = foods.order_by('price')
        drinks = drinks.order_by('price')
    elif sort == 'price_desc':
        fast_foods = fast_foods.order_by('-price')
        foods = foods.order_by('-price')
        drinks = drinks.order_by('-price')
    elif sort == 'name_asc':
        fast_foods = fast_foods.order_by('name')
        foods = foods.order_by('name')
        drinks = drinks.order_by('name')
    elif sort == 'name_desc':
        fast_foods = fast_foods.order_by('-name')
        foods = foods.order_by('-name')
        drinks = drinks.order_by('-name')

    # Fetch all categories for the filter dropdown
    categories = Category.objects.all()

    context = {
        'fast_foods': fast_foods,
        'foods': foods,
        'drinks': drinks,
        'query': query,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    }
    return render(request, 'auths/orders.html', context)

# ✅ Product Detail View
def order(request, item_id, category):
    model_map = {
        'fastfood': FastFood,
        'food': Food,
        'drink': Drink,
    }
    product = get_object_or_404(model_map.get(category), product_id=item_id)
    return render(request, 'auths/order_detail.html', {'product': product})

# ✅ Products View
def products(request):
    return render(request, 'auths/products.html')
# auths/views/product_views.py