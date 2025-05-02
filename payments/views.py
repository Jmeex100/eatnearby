# coreEat/payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponse
from cart.models import Cart, CartItem
from auths.models import FastFood, Food, Drink
from .models import DeliveryInfo, PaymentHistory
from .cards.paypal import initiate_paypal_payment
from .cards.pesapal import initiate_pesapal_payment
from .cards.stripe import initiate_stripe_payment, verify_stripe_payment
from .mobile.airtel import initiate_airtel_payment
from .mobile.zamtel import initiate_zamtel_payment
from .mobile.mtn import initiate_mtn_payment, check_mtn_payment_status
from .mobile.twilio_utils import send_sms  # Import from twilio_utils
import logging

logger = logging.getLogger(__name__)

@login_required
def checkout(request):
    """Handle the checkout process by displaying the form and initiating payments."""
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.cartitem_set.exists():
            messages.warning(request, "Your cart is empty. Add items before checking out.")
            return redirect('cart:cart_view')
    except Cart.DoesNotExist:
        messages.error(request, "No cart found. Please add items to your cart.")
        return redirect('cart:cart_view')

    EXCHANGE_RATE = 28.638  # 1 USD = 28.638 ZMW (March 2025 estimate)
    total_usd = float(cart.total()) / EXCHANGE_RATE
    total_zmw = float(cart.total())

    context = {
        'cart': cart,
        'delivery_points': DeliveryInfo.DELIVERY_POINTS,
        'payment_methods': DeliveryInfo.PAYMENT_METHODS,
        'mobile_money_providers': DeliveryInfo.MOBILE_MONEY_PROVIDERS,
        'card_providers': DeliveryInfo.CARD_PROVIDERS,
        'total_usd': total_usd,
    }

    if request.method == 'POST':
        address = request.POST.get('address', '')
        predefined_address = request.POST.get('predefined_address', '')
        payment_method = request.POST.get('payment_method', 'cash')
        payment_provider = request.POST.get('payment_provider', '')
        phone_number = request.POST.get('phone_number', '')
        secondary_phone_number = request.POST.get('secondary_phone_number', '')

        if not phone_number:
            messages.error(request, "Phone number is required.")
            return render(request, 'payments/checkout.html', context)
        if payment_method in ('mobile_money', 'card') and not payment_provider:
            messages.error(request, f"Please select a provider for {payment_method.replace('_', ' ').title()}.")
            return render(request, 'payments/checkout.html', context)

        delivery_info = DeliveryInfo(
            user=request.user,
            cart=cart,
            address=address if not predefined_address else None,
            predefined_address=predefined_address or None,
            payment_method=payment_method,
            payment_provider=payment_provider or None,
            phone_number=phone_number,
            secondary_phone_number=secondary_phone_number or None,
        )
        delivery_info.save()

        if payment_method == 'card':
            if payment_provider == 'paypal':
                try:
                    paypal_form = initiate_paypal_payment(request, cart, delivery_info, total_usd)
                    return render(request, 'payments/paypal_checkout.html', {'form': paypal_form, 'cart': cart})
                except Exception as e:
                    messages.error(request, f"Paypal payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)
            elif payment_provider == 'pesapal':
                try:
                    pesapal_data = initiate_pesapal_payment(request, cart, delivery_info, total_usd)
                    if pesapal_data.get('status') == 'down':
                        messages.warning(request, pesapal_data['message'])
                        return render(request, 'payments/checkout.html', context)
                    return render(request, 'payments/pesapal_checkout.html', {
                        'iframe_url': pesapal_data['iframe_url'],
                        'cart': cart,
                        'order_id': pesapal_data['order_id'],
                        'total_usd': total_usd,
                    })
                except Exception as e:
                    messages.error(request, f"Pesapal payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)
            elif payment_provider == 'stripe':
                try:
                    stripe_data = initiate_stripe_payment(request, cart, delivery_info, total_usd)
                    request.session['stripe_session_id'] = stripe_data['session_id']
                    return render(request, 'payments/stripe_checkout.html', {
                        'checkout_url': stripe_data['checkout_url'],
                        'total_usd': total_usd,
                    })
                except Exception as e:
                    messages.error(request, f"Stripe payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)

        elif payment_method == 'mobile_money':
            if payment_provider == 'airtel':
                try:
                    airtel_data = initiate_airtel_payment(request, cart, delivery_info, total_zmw)
                    if airtel_data['status'] == 'success':
                        messages.info(request, airtel_data['message'])
                        return render(request, 'payments/airtel_checkout.html', {
                            'phone_number': phone_number,
                            'secondary_phone_number': secondary_phone_number,
                            'total_zmw': total_zmw,
                        })
                    else:
                        messages.warning(request, airtel_data.get('message', 'Airtel payment unavailable.'))
                        return render(request, 'payments/checkout.html', context)
                except Exception as e:
                    messages.error(request, f"Airtel payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)
            elif payment_provider == 'zamtel':
                try:
                    zamtel_data = initiate_zamtel_payment(request, cart, delivery_info, total_zmw)
                    if zamtel_data['status'] == 'success':
                        messages.info(request, zamtel_data['message'])
                        return render(request, 'payments/zamtel_checkout.html', {
                            'phone_number': phone_number,
                            'secondary_phone_number': secondary_phone_number,
                            'total_zmw': total_zmw,
                        })
                    else:
                        messages.warning(request, zamtel_data.get('message', 'Zamtel payment unavailable.'))
                        return render(request, 'payments/checkout.html', context)
                except Exception as e:
                    messages.error(request, f"Zamtel payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)
            elif payment_provider == 'mtn':
                try:
                    mtn_data = initiate_mtn_payment(request, cart, delivery_info, total_zmw, phone_number)
                    if mtn_data['status'] == 'success':
                        messages.info(request, mtn_data['message'])
                        request.session['mtn_transaction_id'] = mtn_data['transaction_id']
                        return render(request, 'payments/mtn_checkout.html', {
                            'phone_number': phone_number,
                            'secondary_phone_number': secondary_phone_number,
                            'total_zmw': total_zmw,
                            'transaction_id': mtn_data['transaction_id'],
                        })
                    else:
                        messages.warning(request, mtn_data.get('message', 'MTN payment unavailable.'))
                        return render(request, 'payments/checkout.html', context)
                except Exception as e:
                    messages.error(request, f"MTN payment initiation failed: {str(e)}")
                    return render(request, 'payments/checkout.html', context)

        return redirect('payments:payment_success')

    return render(request, 'payments/checkout.html', context)


# coreEat/payments/views.py (snippet)
@login_required
@csrf_exempt
def payment_success(request):
    """Process and display payment success confirmation, and send SMS notification."""
    try:
        delivery_info = DeliveryInfo.objects.filter(user=request.user).latest('created_at')
        cart = delivery_info.cart
    except DeliveryInfo.DoesNotExist:
        messages.error(request, "No delivery information found.")
        return redirect('cart:cart_view')

    if request.method == 'POST':
        # [Existing payment processing code unchanged]
        items = [
            {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
            for item in cart.cartitem_set.all()
        ]
        payment_history = PaymentHistory(
            user=request.user,
            cart=cart,
            delivery_info=delivery_info,
            total=cart.total(),
            items=items
        )
        payment_history.save()

        delivery_info.delivery_status = 'completed'
        delivery_info.save()
        cart.cartitem_set.all().delete()

        if 'mtn_transaction_id' in request.session:
            del request.session['mtn_transaction_id']

        # Send SMS notification to +260973546375
        sms_body = (
            f"Order #{payment_history.id} Confirmed!\n"
            f"Total: K{cart.total():.2f}\n"
            f"Delivery to: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
            f"Thank you for ordering with us!"
        )
        sms_result = send_sms('+260973546375', sms_body)  # Hardcoded for testing
        if not sms_result['success']:
            messages.warning(request, f"Order confirmed, but SMS failed: {sms_result['message']}")
        else:
            messages.success(request, "Order confirmed and SMS sent successfully!")

        return render(request, 'payments/success.html', {
            'delivery_info': delivery_info,
            'cart': cart,
            'payment_history': payment_history,
        })

    return render(request, 'payments/success.html', {'delivery_info': delivery_info, 'cart': cart})
@login_required
def payment_done(request):
    """Handle return URL after successful payment from providers like PayPal or Stripe."""
    stripe_session_id = request.session.get('stripe_session_id')
    if stripe_session_id:
        try:
            payment_status = verify_stripe_payment(stripe_session_id)
            if payment_status == 'paid':
                messages.success(request, "Payment successful! Your order is being processed.")
                del request.session['stripe_session_id']
            else:
                messages.error(request, "Payment was not completed. Please try again.")
                return redirect('payments:checkout')
        except Exception as e:
            messages.error(request, f"Payment verification failed: {str(e)}")
            return redirect('payments:checkout')
    else:
        messages.success(request, "Payment successful! Your order is being processed.")

    return redirect('payments:payment_success')


@login_required
def payment_cancelled(request):
    """Handle payment cancellation and redirect to checkout."""
    messages.error(request, "Payment was cancelled. Please try again or choose another method.")
    return redirect('payments:checkout')


@login_required
def order_history(request):
    """Display the user's order history."""
    history = PaymentHistory.objects.filter(user=request.user)
    return render(request, 'payments/order_history.html', {'history': history})


@login_required
def reorder(request, payment_id):
    """Reorder items from a previous order by adding them to the cart."""
    if request.method != 'POST':
        return redirect('payments:order_history')

    payment_history = get_object_or_404(PaymentHistory, id=payment_id, user=request.user)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.cartitem_set.all().delete()

    for item in payment_history.items:
        product = None
        for model in [FastFood, Food, Drink]:
            try:
                product = model.objects.get(name=item['name'])
                break
            except model.DoesNotExist:
                continue

        if product:
            model_name = product.__class__.__name__.lower()
            field_name = 'fast_food' if model_name == 'fastfood' else model_name
            CartItem.objects.create(
                cart=cart,
                **{field_name: product},
                quantity=item['quantity'],
                quality='standard'
            )
        else:
            messages.warning(request, f"Product '{item['name']}' is no longer available.")

    messages.success(request, "Order has been added to your cart!")
    return redirect('cart:cart_view')


@csrf_exempt
def mtn_callback(request):
    """Handle MTN MoMo callback for payment status updates."""
    if request.method == 'PUT':
        try:
            data = request.body.decode('utf-8')
            logger.info(f"MTN Callback received: {data}")
            # TODO: Parse JSON and update PaymentHistory/DeliveryInfo if needed
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"MTN Callback error: {str(e)}")
            return HttpResponse(status=500)
    return HttpResponse(status=405)  # Method Not Allowed