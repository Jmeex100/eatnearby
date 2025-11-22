# Full Code Snippets for Eat Nearby Django Apps

## 1. auths (Users + Products)

### Register View
```python
def register_page(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            user.set_password(password)
            user.save()
            messages.success(request, 'Registration successful!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auths/register_page.html', {'form': form})
```

### Register Template
```html
{% extends 'base.html' %}
{% block content %}
<h2>Register</h2>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Register</button>
</form>
{% endblock %}
```

## 2. sim (Frontend + PWA)

### Home View
```python
def home(request):
    context = {'restaurant_photos': get_restaurant_photos()}
    return render(request, 'home.html', context)
```

### Home Template
```html
{% extends 'base.html' %}
{% block content %}
<h1>Welcome to Eat Nearby</h1>
{% for photo in restaurant_photos %}
<img src="{{ photo }}" alt="Restaurant">
{% endfor %}
{% endblock %}
```

## 3. community (Posts, Reviews, Recipes, Challenges, Q&A)

### Restaurant List View
```python
def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})
```

### Restaurant List Template
```html
{% extends "community_base.html" %}
{% block content %}
<h1>Restaurants</h1>
{% for restaurant in restaurants %}
<p>{{ restaurant.name }}</p>
{% endfor %}
{% endblock %}
```

## 5. payments (Delivery + Payment Systems)

### Checkout View
```python
@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    if request.method == 'POST':
        # Process order
        messages.success(request, "Order placed!")
        return redirect('payments:payment_success', delivery_id=1)
    context = {'cart': cart}
    return render(request, 'payments/checkout.html', context)
```

### Checkout Template
```html
{% extends 'base.html' %}
{% block content %}
<h1>Checkout</h1>
<form method="post">
    {% csrf_token %}
    <button type="submit">Place Order</button>
</form>
{% endblock %}
```

## 6. staffs (Staff Assignment + Notifications)

### Dashboard View
```python
@login_required
def dashboard(request):
    stats = StaffAssignment.objects.filter(staff=request.user).aggregate(
        active=Count('id', filter=Q(delivery__delivery_status='in_progress')),
        completed=Count('id', filter=Q(delivery__delivery_status='completed'))
    )
    context = {'stats': stats}
    return render(request, 'staffs/dashboard.html', context)
```

### Dashboard Template
```html
{% extends 'staffs/base.html' %}
{% block content %}
<h1>Staff Dashboard</h1>
<p>Active: {{ stats.active }}</p>
<p>Completed: {{ stats.completed }}</p>
{% endblock %}
```

## 7. superadmin (Admin Dashboard)

### Dashboard View
```python
@superadmin_required
def dashboard(request):
    user_count = User.objects.count()
    delivery_count = DeliveryInfo.objects.count()
    context = {'user_count': user_count, 'delivery_count': delivery_count}
    return render(request, 'superadmin/dashboard.html', context)
```

### Dashboard Template
```html
{% extends 'superadmin/base.html' %}
{% block content %}
<h1>SuperAdmin Dashboard</h1>
<p>Total Users: {{ user_count }}</p>
<p>Total Deliveries: {{ delivery_count }}</p>
{% endblock %}