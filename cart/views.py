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
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
        else:
            product_id = request.POST.get('product_id') or request.path.split('/')[-2]
            quantity = int(request.POST.get('quantity', 1))

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

        model_name = product.__class__.__name__.lower()
        field_name = 'fast_food' if model_name == 'fastfood' else model_name

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            **{field_name: product},
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
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

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'subtotal': float(cart_item.subtotal()),
            'cart_total': float(cart.total()),
            'cart_count': cart.cartitem_set.count()
        })
    return JsonResponse({'success': False, 'error': 'Invalid request'})