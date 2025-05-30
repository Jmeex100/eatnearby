# staffs/pos_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from auths.models import User, FastFood, Food, Drink
from payments.models import DeliveryInfo, PaymentHistory
from cart.models import Cart, CartItem
import json
from .staffs_decorator import staff_view
import logging

logger = logging.getLogger(__name__)

@staff_view
@login_required
def sales(request):
    # Fetch all products for POS interface
    fast_foods = FastFood.objects.all()
    foods = Food.objects.all()
    drinks = Drink.objects.all()
    
    # Combine products for display and set product_type
    products = []
    for product in list(fast_foods) + list(foods) + list(drinks):
        if isinstance(product, FastFood):
            product.product_type = 'fastfood'
        elif isinstance(product, Food):
            product.product_type = 'food'
        elif isinstance(product, Drink):
            product.product_type = 'drink'
        products.append(product)
    
    # Handle order creation
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create a cart for the POS order
                cart = Cart.objects.create(user=request.user)
                
                # Process selected items
                items = json.loads(request.POST.get('items', '[]'))
                subtotal = 0
                cart_items = []
                
                for item in items:
                    product_type = item.get('type')
                    product_id = item.get('product_id')
                    quantity = int(item.get('quantity', 1))
                    
                    # Fetch the product based on type
                    product = None
                    if product_type == 'fastfood':
                        product = FastFood.objects.get(product_id=product_id)
                    elif product_type == 'food':
                        product = Food.objects.get(product_id=product_id)
                    elif product_type == 'drink':
                        product = Drink.objects.get(product_id=product_id)
                    else:
                        raise ValueError(f"Invalid product type: {product_type}")
                    
                    if product.quantity < quantity:
                        raise ValueError(f"Insufficient stock for {product.name}")
                    
                    item_subtotal = product.price * quantity
                    subtotal += item_subtotal
                    cart_items.append({
                        'name': product.name,
                        'quantity': quantity,
                        'subtotal': float(item_subtotal)
                    })
                    
                    # Add to cart
                    cart_item_data = {
                        'cart': cart,
                        'quantity': quantity,
                        'quality': 'standard',  # Default value; adjust if needed
                    }
                    if product_type == 'fastfood':
                        cart_item_data['fast_food'] = product
                    elif product_type == 'food':
                        cart_item_data['food'] = product
                    elif product_type == 'drink':
                        cart_item_data['drink'] = product
                    
                    CartItem.objects.create(**cart_item_data)
                    
                    # Update product quantity
                    product.quantity -= quantity
                    product.save()
                
                # Calculate tax (10% as per template)
                tax = subtotal
                total = subtotal + tax
                
                # Get payment method and provider
                payment_method = request.POST.get('payment_method', 'cash')
                payment_provider = request.POST.get('payment_provider', None)
                
                # Validate payment provider for mobile_money
                if payment_method == 'mobile_money' and payment_provider not in ['airtel', 'mtn', 'zamtel']:
                    raise ValueError("Invalid mobile money provider")
                
                # Create DeliveryInfo (in-store POS order)
                delivery_info = DeliveryInfo.objects.create(
                    user=request.user,
                    cart=cart,
                    is_pos_order=True,
                    payment_method=payment_method,
                    payment_provider=payment_provider if payment_method == 'mobile_money' else None,
                    phone_number=request.POST.get('phone_number', ''),
                    delivery_status='completed'  # POS orders are completed immediately
                )
                
                # Create PaymentHistory
                PaymentHistory.objects.create(
                    user=request.user,
                    cart=cart,
                    delivery_info=delivery_info,
                    total=total,
                    items=cart_items
                )
                
                messages.success(request, "Order processed successfully!")
                return redirect('staffs:sales')
                
        except Exception as e:
            logger.error(f"Error processing POS order: {str(e)}")
            messages.error(request, f"Error processing order: {str(e)}")
    
    context = {
        'products': products,
        'payment_methods': [
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
        ],
    }
    return render(request, 'sales/sales.html', context)