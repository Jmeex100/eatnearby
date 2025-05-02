from django.shortcuts import render, get_object_or_404
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