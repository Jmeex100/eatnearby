import qrcode
import io
import base64
import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from django.utils.timezone import now
from django.core.paginator import Paginator
from typing import Dict, Optional
from cart.models import Cart, CartItem
from auths.models import FastFood, Food, Drink
from .models import DeliveryInfo, PaymentHistory
from staffs.models import StaffAssignment, Notification
from staffs.staffs_assignments import pick_staff_for_point
from .cards.paypal import initiate_paypal_payment
from .cards.pesapal import initiate_pesapal_payment, verify_pesapal_payment
from .cards.stripe import initiate_stripe_payment, verify_stripe_payment
from .mobile.airtel import initiate_airtel_payment
from .mobile.zamtel import initiate_zamtel_payment
from .mobile.mtn import initiate_mtn_payment
from .mobile.twilio_utils import send_sms

logger = logging.getLogger(__name__)

EXCHANGE_RATE = 28.638  # 1 USD = 28.638 ZMW (March 2025)

def clear_payment_session(request) -> None:
    """Clear payment-related session keys."""
    keys = [
        'mobile_order_data', 'mobile_transaction_id', 'stripe_session_id',
        'paypal_order_data', 'pesapal_order_data', 'pesapal_order_id',
        'stripe_order_data', 'pending_order'
    ]
    for key in keys:
        request.session.pop(key, None)

def generate_qr_code(delivery_info: DeliveryInfo, payment_history: Optional[PaymentHistory], cart: Cart) -> Optional[str]:
    """Generate a base64-encoded QR code for order details."""
    try:
        qr_data = (
            f"Order ID: {delivery_info.id}\n"
            f"Payment ID: {payment_history.id if payment_history else 'Pending'}\n"
            f"Ordered By: {delivery_info.user.username}\n"
            f"Delivery Location: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
            f"Total: K{payment_history.total if payment_history else cart.total():.2f}\n"
            f"Track: https://eatnearby.com/track/{delivery_info.id}"
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to generate QR code for delivery {delivery_info.id}: {str(e)}")
        return None

def create_delivery_info(request, order_data: Dict, cart: Cart) -> DeliveryInfo:
    """Create DeliveryInfo and assign staff."""
    try:
        with transaction.atomic():
            delivery_info = DeliveryInfo.objects.create(
                user=request.user,
                cart=cart,
                address=order_data['address'] if not order_data['predefined_address'] else None,
                predefined_address=order_data['predefined_address'],
                payment_method=order_data['payment_method'],
                payment_provider=order_data.get('payment_provider'),
                phone_number=order_data['phone_number'],
                secondary_phone_number=order_data.get('secondary_phone_number'),
            )
            logger.info(f"Created DeliveryInfo {delivery_info.id} with status {delivery_info.delivery_status}")

            staff = pick_staff_for_point(delivery_info.predefined_address)
            if staff:
                StaffAssignment.objects.create(staff=staff, delivery=delivery_info)
                Notification.objects.create(
                    recipient=staff,
                    message=f"New delivery at {delivery_info.get_predefined_address_display()} (Order ID: {delivery_info.id})",
                    related_delivery=delivery_info,
                    notification_type='new_order'
                )
                logger.info(f"Assigned delivery {delivery_info.id} to staff {staff.id}")
            else:
                logger.warning(f"No staff available for delivery {delivery_info.id}")

            return delivery_info
    except Exception as e:
        logger.error(f"Failed to create DeliveryInfo: {str(e)}")
        raise

def create_payment_history(user, cart: Cart, delivery_info: DeliveryInfo, transaction_id: str) -> PaymentHistory:
    """Create PaymentHistory for an order."""
    items = [
        {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
        for item in cart.cartitem_set.all()
    ]
    return PaymentHistory.objects.create(
        user=user,
        cart=cart,
        delivery_info=delivery_info,
        total=cart.total(),
        items=items,
        transaction_id=transaction_id
    )

def validate_checkout_data(request, payment_method: str, payment_provider: str, phone_number: str, predefined_address: str) -> Optional[str]:
    """Validate checkout form data."""
    if not phone_number:
        return "Phone number is required."
    if payment_method in ('mobile_money', 'card') and not payment_provider:
        return f"Select a provider for {payment_method.replace('_', ' ').title()}."
    if not predefined_address:
        return "Please select a delivery point."
    return None

@login_required
def checkout(request):
    """Handle checkout process for cart items."""
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.cartitem_set.exists():
            messages.warning(request, "Your cart is empty. Add items before checking out.")
            return redirect('cart:cart_view')
    except Cart.DoesNotExist:
        messages.error(request, "No cart found. Please add items to your cart.")
        return redirect('cart:cart_view')

    total_usd = float(cart.total()) / EXCHANGE_RATE
    total_zmw = float(cart.total())

    context = {
        'cart': cart,
        'delivery_points': DeliveryInfo.DELIVERY_POINTS,
        'payment_methods': DeliveryInfo.PAYMENT_METHODS,
        'mobile_money_providers': DeliveryInfo.MOBILE_MONEY_PROVIDERS,
        'card_providers': DeliveryInfo.CARD_PROVIDERS,
        'total_usd': total_usd,
        'total_zmw': total_zmw,
    }

    if request.method == 'POST':
        address = request.POST.get('address', '')
        predefined_address = request.POST.get('predefined_address', '')
        payment_method = request.POST.get('payment_method', 'cash')
        payment_provider = request.POST.get('payment_provider', '')
        phone_number = request.POST.get('phone_number', '')
        secondary_phone_number = request.POST.get('secondary_phone_number', '')

        error = validate_checkout_data(request, payment_method, payment_provider, phone_number, predefined_address)
        if error:
            messages.error(request, error)
            return render(request, 'payments/checkout.html', context)

        order_data = {
            'cart_id': cart.id,
            'address': address,
            'predefined_address': predefined_address,
            'payment_method': payment_method,
            'payment_provider': payment_provider or None,
            'phone_number': phone_number,
            'secondary_phone_number': secondary_phone_number or None,
        }
        request.session['pending_order'] = order_data

        try:
            if payment_method == 'card':
                if payment_provider == 'paypal':
                    form = initiate_paypal_payment(request, cart, None, total_usd)
                    request.session['paypal_order_data'] = order_data
                    return render(request, 'payments/paypal_checkout.html', {'form': form, 'cart': cart})
                elif payment_provider == 'pesapal':
                    pesapal_data = initiate_pesapal_payment(request, cart, None, total_usd)
                    if pesapal_data.get('status') == 'down':
                        messages.warning(request, pesapal_data['message'])
                        clear_payment_session(request)
                        return render(request, 'payments/checkout.html', context)
                    request.session['pesapal_order_data'] = order_data
                    request.session['pesapal_order_id'] = pesapal_data['order_id']
                    return render(request, 'payments/pesapal_checkout.html', {
                        'iframe_url': pesapal_data['iframe_url'],
                        'cart': cart,
                        'order_id': pesapal_data['order_id'],
                        'total_usd': total_usd,
                    })
                elif payment_provider == 'stripe':
                    stripe_data = initiate_stripe_payment(request, cart, None, total_usd)
                    request.session['stripe_session_id'] = stripe_data['session_id']
                    request.session['stripe_order_data'] = order_data
                    return render(request, 'payments/stripe_checkout.html', stripe_data)
            elif payment_method == 'mobile_money':
                mobile_payment_map = {
                    'airtel': initiate_airtel_payment,
                    'zamtel': initiate_zamtel_payment,
                    'mtn': lambda *args: initiate_mtn_payment(*args, phone_number=phone_number)
                }
                data = mobile_payment_map[payment_provider](request, cart, None, total_zmw)
                if data['status'] == 'success':
                    messages.info(request, data['message'])
                    request.session['mobile_order_data'] = order_data
                    request.session['mobile_transaction_id'] = data.get('transaction_id')
                    template_map = {
                        'airtel': 'payments/airtel_checkout.html',
                        'zamtel': 'payments/zamtel_checkout.html',
                        'mtn': 'payments/mtn_checkout.html',
                    }
                    return render(request, template_map[payment_provider], {
                        'phone_number': phone_number,
                        'secondary_phone_number': secondary_phone_number,
                        'total_zmw': total_zmw,
                        'transaction_id': data.get('transaction_id'),
                    })
                else:
                    messages.warning(request, data.get('message', f"{payment_provider.upper()} payment failed."))
                    clear_payment_session(request)
            else:  # Cash payment
                delivery_info = create_delivery_info(request, order_data, cart)
                payment_history = create_payment_history(
                    request.user, cart, delivery_info, f"CASH-{str(uuid.uuid4())[:8]}"
                )
                logger.info(f"Created PaymentHistory {payment_history.id} for cash order")
                messages.success(request, "Your cash order has been placed successfully.")
                clear_payment_session(request)
                return redirect('payments:payment_success', delivery_id=delivery_info.id)
        except Exception as e:
            logger.error(f"{payment_method.title()} order processing failed: {str(e)}")
            messages.error(request, f"Order processing failed: {str(e)}")
            clear_payment_session(request)
            return render(request, 'payments/checkout.html', context)

    return render(request, 'payments/checkout.html', context)

@login_required
@csrf_exempt
def simulate_mobile_payment(request, provider: str):
    """Process mobile money payments for Airtel, Zamtel, or MTN."""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('payments:checkout')

    phone = request.POST.get('phone') or request.POST.get('mtn_number')
    amount = request.POST.get('amount')
    order_data = request.session.get('mobile_order_data')
    transaction_id = request.session.get('mobile_transaction_id')

    if not order_data or not transaction_id:
        messages.error(request, "Invalid session. Please try again.")
        logger.warning(f"{provider.upper()} payment attempted with no order_data or transaction_id")
        return redirect('payments:checkout')

    if not phone or not amount:
        messages.error(request, "Missing payment details.")
        logger.warning(f"{provider.upper()} payment attempted with missing phone or amount")
        return redirect('payments:checkout')

    try:
        cart = Cart.objects.get(id=order_data['cart_id'], user=request.user)
        delivery_info = create_delivery_info(request, order_data, cart)
        payment_history = create_payment_history(
            request.user, cart, delivery_info, f"{provider.upper()}-{transaction_id or str(uuid.uuid4())}"
        )
        logger.info(f"{provider.title()} payment for {phone}, Amount: {amount} ZMW, Delivery {delivery_info.id}")
        messages.success(request, f"{provider.title()} payment successful!")
        clear_payment_session(request)
        return redirect('payments:payment_success', delivery_id=delivery_info.id)
    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        logger.error(f"Cart {order_data['cart_id']} not found for {provider.upper()} payment")
        return redirect('payments:checkout')
    except Exception as e:
        logger.error(f"{provider.title()} payment processing failed: {str(e)}")
        messages.error(request, f"Payment processing failed: {str(e)}")
        return redirect('payments:checkout')

# Aliases for mobile payment providers
airtel_payment_process = lambda request: simulate_mobile_payment(request, 'airtel')
zamtel_payment_process = lambda request: simulate_mobile_payment(request, 'zamtel')
mtn_payment_process = lambda request: simulate_mobile_payment(request, 'mtn')

@login_required
@csrf_exempt
def payment_success(request, delivery_id: int):
    """Handle order confirmation and display success page with QR code."""
    delivery_info = get_object_or_404(DeliveryInfo, id=delivery_id, user=request.user)
    cart = delivery_info.cart
    payment_history = PaymentHistory.objects.filter(delivery_info=delivery_info).first()

    qr_image_base64 = generate_qr_code(delivery_info, payment_history, cart)
    if not qr_image_base64:
        messages.warning(request, "Unable to generate QR code due to an error.")

    if request.method == 'POST' and delivery_info.delivery_status == 'in_progress':
        try:
            with transaction.atomic():
                delivery_info.delivery_status = 'completed'
                delivery_info.save()

                staff_assignment = StaffAssignment.objects.filter(delivery=delivery_info).first()
                if staff_assignment:
                    Notification.objects.create(
                        recipient=staff_assignment.staff,
                        message=f"Delivery at {delivery_info.get_predefined_address_display()} confirmed by customer.",
                        related_delivery=delivery_info,
                        notification_type='delivery_completed'
                    )

                total_amount = cart.total() if cart else 0.00
                if cart:
                    cart.cartitem_set.all().delete()

                sms_body = (
                    f"Order #{payment_history.id if payment_history else delivery_info.id} Confirmed!\n"
                    f"Total: K{total_amount:.2f}\n"
                    f"Delivery to: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
                    f"Thank you for ordering with us!"
                )
                send_sms(delivery_info.phone_number, sms_body)

                messages.success(request, f"Order confirmed! SMS sent to {delivery_info.phone_number}")
                logger.info(f"Delivery {delivery_id} confirmed by user {request.user.username}")

        except Exception as e:
            logger.error(f"Error confirming delivery {delivery_id}: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect('payments:payment_success', delivery_id=delivery_id)

    context = {
        'delivery_info': delivery_info,
        'cart': cart,
        'payment_history': payment_history,
        'qr_image': qr_image_base64,
        'current_date': now().strftime('%B %d, %Y'),
        'current_time': now().strftime('%I:%M %p'),
    }
    return render(request, 'payments/success.html', context)

@login_required
@csrf_exempt
def payment_done(request):
    """Handle payment completion for PayPal, Stripe, and Pesapal."""
    logger.debug(f"payment_done called: session_keys={list(request.session.keys())}, session_id={request.session.session_key}")

    def process_payment(order_data: Dict, provider: str, transaction_id: str) -> Optional[redirect]:
        try:
            cart = Cart.objects.get(id=order_data['cart_id'], user=request.user)
            delivery_info = create_delivery_info(request, order_data, cart)
            payment_history = create_payment_history(request.user, cart, delivery_info, transaction_id)
            delivery_info.delivery_status = 'pending'
            delivery_info.save()
            messages.success(request, f"{provider.title()} payment successful!")
            clear_payment_session(request)
            return redirect('payments:payment_success', delivery_id=delivery_info.id)
        except Cart.DoesNotExist:
            logger.error(f"Cart {order_data['cart_id']} not found for {provider} payment")
            messages.error(request, "Invalid payment session: Cart not found.")
            return redirect('payments:checkout')
        except Exception as e:
            logger.error(f"{provider} payment processing failed: {str(e)}")
            messages.error(request, f"Payment processing failed: {str(e)}")
            return redirect('payments:checkout')

    # PayPal
    paypal_order_data = request.session.get('paypal_order_data')
    if paypal_order_data:
        return process_payment(paypal_order_data, "PayPal", f"PAYPAL-PENDING-{str(uuid.uuid4())[:8]}")

    # Stripe
    stripe_session_id = request.session.get('stripe_session_id')
    stripe_order_data = request.session.get('stripe_order_data')
    if not (stripe_session_id and stripe_order_data):
        session_key = request.GET.get('session_key')
        if session_key and session_key == request.session.session_key:
            stripe_session_id = request.session.get('stripe_session_id')
            stripe_order_data = request.session.get('stripe_order_data')
            logger.debug(f"Stripe session restored via query param: session_id={stripe_session_id}")
        else:
            logger.error(f"Stripe session missing: session_id={stripe_session_id}, query_session_key={session_key}")
            messages.error(request, "Invalid payment session.")
            return redirect('payments:checkout')

    if stripe_session_id and stripe_order_data:
        try:
            status = verify_stripe_payment(stripe_session_id)
            if status == 'paid':
                return process_payment(stripe_order_data, "Stripe", f"STRIPE-{str(uuid.uuid4())}")
            else:
                logger.warning(f"Stripe payment not completed: status={status}")
                messages.error(request, "Stripe payment was not completed.")
                return redirect('payments:checkout')
        except Exception as e:
            logger.error(f"Stripe payment verification failed: {str(e)}")
            messages.error(request, f"Payment verification failed: {str(e)}")
            return redirect('payments:checkout')

    # Pesapal
    pesapal_order_data = request.session.get('pesapal_order_data')
    pesapal_order_id = request.session.get('pesapal_order_id')
    if pesapal_order_data and pesapal_order_id:
        try:
            status = verify_pesapal_payment(pesapal_order_id)
            if status == 'paid':
                return process_payment(pesapal_order_data, "Pesapal", f"PESAPAL-{pesapal_order_id}")
            else:
                messages.error(request, "Pesapal payment was not completed.")
                return redirect('payments:checkout')
        except Exception as e:
            logger.error(f"Pesapal payment verification failed: {str(e)}")
            messages.error(request, f"Payment verification failed: {str(e)}")
            return redirect('payments:checkout')

    logger.error("Invalid payment session: No valid session data found")
    messages.error(request, "Invalid payment session.")
    return redirect('payments:checkout')

@login_required
@csrf_exempt
def payment_cancelled(request):
    """Handle payment cancellation."""
    clear_payment_session(request)
    messages.error(request, "Payment was cancelled.")
    return redirect('payments:checkout')

@login_required
def order_history(request):
    """Display the user's order history with pagination."""
    history = PaymentHistory.objects.filter(user=request.user).select_related('cart', 'delivery_info')
    paginator = Paginator(history, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'payments/order_history.html', {'history': page_obj, 'page_obj': page_obj})

@login_required
def reorder(request, payment_id: int):
    """Reorder a previous order by adding items to the cart."""
    if request.method != 'POST':
        return redirect('payments:order_history')

    payment_history = get_object_or_404(PaymentHistory, id=payment_id, user=request.user)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.cartitem_set.all().delete()

    for item in payment_history.items:
        for model in [FastFood, Food, Drink]:
            try:
                product = model.objects.get(name=item['name'])
                model_field = 'fast_food' if model.__name__ == 'FastFood' else model.__name__.lower()
                CartItem.objects.create(cart=cart, **{model_field: product}, quantity=item['quantity'], quality='standard')
                break
            except model.DoesNotExist:
                continue
        else:
            messages.warning(request, f"Product '{item['name']}' is no longer available.")

    messages.success(request, "Order has been added to your cart!")
    return redirect('cart:cart_view')

@csrf_exempt
def mtn_callback(request):
    """Handle MTN payment callback."""
    if request.method == 'PUT':
        try:
            data = request.body.decode('utf-8')
            logger.info(f"MTN Callback received: {data}")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"MTN Callback error: {str(e)}")
            return HttpResponse(status=500)
    return HttpResponse(status=405)

@login_required
@csrf_exempt
def in_progress_orders(request):
    """Display in-progress and cancelled orders for the customer."""
    in_progress_orders = DeliveryInfo.objects.filter(
        user=request.user,
        delivery_status='in_progress'
    ).select_related('cart', 'user').prefetch_related('cart__cartitem_set', 'payment_histories')

    declined_orders = DeliveryInfo.objects.filter(
        user=request.user,
        delivery_status='cancelled'
    ).select_related('cart', 'user').prefetch_related('cart__cartitem_set', 'payment_histories', 'notifications')

    if request.method == 'POST':
        if 'delivery_id' in request.POST:
            delivery_id = request.POST.get('delivery_id')
            try:
                with transaction.atomic():
                    delivery_info = get_object_or_404(
                        DeliveryInfo, id=delivery_id, user=request.user, delivery_status='in_progress'
                    )
                    delivery_info.delivery_status = 'completed'
                    delivery_info.save()

                    staff_assignment = StaffAssignment.objects.filter(delivery=delivery_info).first()
                    if staff_assignment:
                        Notification.objects.create(
                            recipient=staff_assignment.staff,
                            message=f"Delivery at {delivery_info.get_predefined_address_display()} confirmed by customer.",
                            related_delivery=delivery_info,
                            notification_type='delivery_completed'
                        )

                    cart = delivery_info.cart
                    if cart:
                        cart.cartitem_set.all().delete()

                    payment_history = PaymentHistory.objects.filter(delivery_info=delivery_info).first()
                    order_reference = payment_history.id if payment_history else delivery_info.id
                    total_amount = payment_history.total if payment_history else cart.total() if cart else 0.00

                    sms_body = (
                        f"Order #{order_reference} Confirmed!\n"
                        f"Total: K{total_amount:.2f}\n"
                        f"Delivery to: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
                        f"Thank you for ordering with us!"
                    )
                    send_sms(delivery_info.phone_number, sms_body)

                    messages.success(request, f"Order {delivery_id} confirmed! SMS sent to {delivery_info.phone_number}")
                    logger.info(f"Delivery {delivery_id} confirmed by user {request.user.username}")

            except Exception as e:
                logger.error(f"Error confirming delivery {delivery_id}: {str(e)}")
                messages.error(request, f"Error confirming order: {str(e)}")

        elif 'delete_delivery_id' in request.POST:
            delete_delivery_id = request.POST.get('delete_delivery_id')
            try:
                with transaction.atomic():
                    delivery_info = get_object_or_404(
                        DeliveryInfo, id=delete_delivery_id, user=request.user, delivery_status='cancelled'
                    )
                    delivery_info.delete()
                    messages.success(request, f"Order {delete_delivery_id} deleted successfully.")
                    logger.info(f"Delivery {delete_delivery_id} deleted by user {request.user.username}")

            except Exception as e:
                logger.error(f"Error deleting delivery {delete_delivery_id}: {str(e)}")
                messages.error(request, f"Error deleting order: {str(e)}")

        return redirect('payments:in_progress_orders')

    context = {
        'in_progress_orders': in_progress_orders,
        'declined_orders': declined_orders,
    }
    return render(request, 'payments/in_progress_orders.html', context)



from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import DeliveryInfo
import logging
from geopy.geocoders import Nominatim

def geocode_address(address):
    """
    Convert a custom address to coordinates using Nominatim geocoding service.
    
    Args:
        address (str): The address to geocode.
    
    Returns:
        dict: Dictionary with 'lat' and 'lng' keys, or None if geocoding fails.
    """
    try:
        geolocator = Nominatim(user_agent="eatnearby")
        location = geolocator.geocode(address + ", Lusaka, Zambia")
        if location:
            return {"lat": location.latitude, "lng": location.longitude}
        logger.warning(f"Geocoding failed for address: {address}")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for address {address}: {str(e)}")
        return None

@login_required
def get_delivery_locations(request, delivery_id: int):
    try:
        delivery = get_object_or_404(DeliveryInfo, id=delivery_id, user=request.user)
        # Access DELIVERY_POINTS_COORDS via the DeliveryInfo class
        destination_coords = DeliveryInfo.DELIVERY_POINTS_COORDS.get(delivery.predefined_address, None)
        if delivery.address and not destination_coords:
            destination_coords = geocode_address(delivery.address)
        response_data = {
            'status': 'success',
            'restaurant': delivery.restaurant_location,
            'driver': delivery.driver_location,
            'destination': {
                'address': delivery.address or delivery.get_predefined_address_display(),
                'coords': destination_coords
            }
        }
        return JsonResponse(response_data)
    except DeliveryInfo.DoesNotExist:
        logger.warning(f"Delivery {delivery_id} not found for user {request.user.id}")
        return JsonResponse({'status': 'error', 'message': 'Delivery not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching delivery locations for {delivery_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)