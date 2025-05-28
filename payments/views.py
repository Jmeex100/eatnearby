# Qrcode 
import qrcode
import io
import base64
import logging
import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from cart.models import Cart, CartItem
from auths.models import FastFood, Food, Drink
from .models import DeliveryInfo, PaymentHistory
from staffs.models import StaffAssignment, Notification
from staffs.staffs_assignments import pick_staff_for_point

# Payment integrations
from django.db import transaction
from .cards.paypal import initiate_paypal_payment
from .cards.pesapal import initiate_pesapal_payment, verify_pesapal_payment
from .cards.stripe import initiate_stripe_payment, verify_stripe_payment
from .mobile.airtel import initiate_airtel_payment
from .mobile.zamtel import initiate_zamtel_payment
from .mobile.mtn import initiate_mtn_payment
from .mobile.twilio_utils import send_sms

logger = logging.getLogger(__name__)


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.cartitem_set.exists():
            messages.warning(request, "Your cart is empty. Add items before checking out.")
            return redirect('cart:cart_view')
    except Cart.DoesNotExist:
        messages.error(request, "No cart found. Please add items to your cart.")
        return redirect('cart:cart_view')

    EXCHANGE_RATE = 28.638  # 1 USD = 28.638 ZMW (March 2025)
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

        if not phone_number:
            messages.error(request, "Phone number is required.")
            return render(request, 'payments/checkout.html', context)
        if payment_method in ('mobile_money', 'card') and not payment_provider:
            messages.error(request, f"Select a provider for {payment_method.replace('_', ' ').title()}.")
            return render(request, 'payments/checkout.html', context)
        if not predefined_address:
            messages.error(request, "Please select a delivery point.")
            return render(request, 'payments/checkout.html', context)

        # Store order details in session for non-cash payments
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

        # Handle card payments
        if payment_method == 'card':
            try:
                if payment_provider == 'paypal':
                    form = initiate_paypal_payment(request, cart, None, total_usd)
                    request.session['paypal_order_data'] = order_data
                    return render(request, 'payments/paypal_checkout.html', {'form': form, 'cart': cart})
                elif payment_provider == 'pesapal':
                    pesapal_data = initiate_pesapal_payment(request, cart, None, total_usd)
                    if pesapal_data.get('status') == 'down':
                        messages.warning(request, pesapal_data['message'])
                        request.session.pop('pending_order', None)
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
            except Exception as e:
                logger.error(f"{payment_provider.title()} payment initiation failed: {str(e)}")
                messages.error(request, f"{payment_provider.title()} payment failed: {str(e)}")
                request.session.pop('pending_order', None)
                return render(request, 'payments/checkout.html', context)

        # Handle mobile money payments
        elif payment_method == 'mobile_money':
            try:
                if payment_provider == 'airtel':
                    data = initiate_airtel_payment(request, cart, None, total_zmw)
                elif payment_provider == 'zamtel':
                    data = initiate_zamtel_payment(request, cart, None, total_zmw)
                elif payment_provider == 'mtn':
                    data = initiate_mtn_payment(request, cart, None, total_zmw, phone_number)

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
                    request.session.pop('pending_order', None)
            except Exception as e:
                logger.error(f"{payment_provider.title()} payment failed: {str(e)}")
                messages.error(request, f"{payment_provider.title()} payment failed: {str(e)}")
                request.session.pop('pending_order', None)
            return render(request, 'payments/checkout.html', context)

        # Cash payment
        try:
            delivery_info = DeliveryInfo.objects.create(
                user=request.user,
                cart=cart,
                address=address if not predefined_address else None,
                predefined_address=predefined_address,
                payment_method=payment_method,
                payment_provider=payment_provider or None,
                phone_number=phone_number,
                secondary_phone_number=secondary_phone_number or None,
            )
            logger.info(f"Created DeliveryInfo {delivery_info.id} for cash order with status {delivery_info.delivery_status}")

            # Create PaymentHistory for cash payment
            items = [
                {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                for item in cart.cartitem_set.all()
            ]
            payment_history = PaymentHistory.objects.create(
                user=request.user,
                cart=cart,
                delivery_info=delivery_info,
                total=cart.total(),
                items=items,
                transaction_id=f"CASH-{str(uuid.uuid4())[:8]}"
            )
            logger.info(f"Created PaymentHistory {payment_history.id} for cash order")

            staff = pick_staff_for_point(delivery_info.predefined_address)
            if staff:
                StaffAssignment.objects.create(staff=staff, delivery=delivery_info)
                Notification.objects.create(
                    recipient=staff,
                    message=f"New cash delivery at {delivery_info.get_predefined_address_display()} (Order ID: {delivery_info.id})",
                    related_delivery=delivery_info,
                    notification_type='new_order'
                )
                logger.info(f"Assigned cash delivery {delivery_info.id} to staff {staff.id}")
            else:
                logger.warning(f"No staff available for cash delivery {delivery_info.id}")

            messages.success(request, "Your cash order has been placed successfully.")
            request.session.pop('pending_order', None)
            return redirect('payments:payment_success', delivery_id=delivery_info.id)

        except Exception as e:
            logger.error(f"Cash order processing failed: {str(e)}")
            messages.error(request, f"Cash order failed: {str(e)}")
            request.session.pop('pending_order', None)
            return render(request, 'payments/checkout.html', context)

    return render(request, 'payments/checkout.html', context)
def create_delivery_info(request, order_data, cart):
    """Helper function to create DeliveryInfo and assign staff."""
    try:
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

# Payment processing views for Airtel, Zamtel, MTN
@login_required
@csrf_exempt
def simulate_mobile_payment(request, provider):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('payments:checkout')

    phone = request.POST.get('phone') or request.POST.get('mtn_number')
    amount = request.POST.get('amount')
    order_data = request.session.get('mobile_order_data')
    transaction_id = request.session.get('mobile_transaction_id')

    if not order_data or not transaction_id:
        messages.error(request, "Invalid session. Please try again.")
        logger.warning(f"{provider.upper()} payment attempted with no order_data or transaction_id in session")
        return redirect('payments:checkout')

    if not phone or not amount:
        messages.error(request, "Missing payment details.")
        logger.warning(f"{provider.upper()} payment attempted with missing phone or amount")
        return redirect('payments:checkout')

    try:
        cart = Cart.objects.get(id=order_data['cart_id'], user=request.user)
        delivery_info = create_delivery_info(request, order_data, cart)

        items = [
            {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
            for item in cart.cartitem_set.all()
        ]
        payment_history = PaymentHistory.objects.create(
            user=request.user,
            cart=cart,
            delivery_info=delivery_info,
            total=cart.total(),
            items=items,
            transaction_id=f"{provider.upper()}-{transaction_id or str(uuid.uuid4())}"
        )

        logger.info(f"{provider.title()} payment for {phone}, Amount: {amount} ZMW, Delivery {delivery_info.id}")
        messages.success(request, f"{provider.title()} payment successfully!")

        # Clear session
        for key in ['mobile_order_data', 'mobile_transaction_id', 'pending_order']:
            request.session.pop(key, None)

        return redirect('payments:payment_success', delivery_id=delivery_info.id)

    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        logger.error(f"Cart {order_data['cart_id']} not found for {provider.upper()} payment")
        return redirect('payments:checkout')
    except Exception as e:
        logger.error(f"{provider.title()} payment processing failed: {str(e)}")
        messages.error(request, f"Payment processing failed: {str(e)}")
        return redirect('payments:checkout')

# Aliases for each provider
airtel_payment_process = lambda request: simulate_mobile_payment(request, 'airtel')
zamtel_payment_process = lambda request: simulate_mobile_payment(request, 'zamtel')
mtn_payment_process = lambda request: simulate_mobile_payment(request, 'mtn')

@login_required
@csrf_exempt
def payment_success(request, delivery_id):
    delivery_info = get_object_or_404(DeliveryInfo, id=delivery_id, user=request.user)
    cart = delivery_info.cart
    payment_history = PaymentHistory.objects.filter(delivery_info=delivery_info).first()

    # Generate QR code with order details
    qr_image_base64 = None
    try:
        qr_data = (
            f"Order ID: {delivery_info.id}\n"
            f"Payment ID: {payment_history.id if payment_history else 'Pending'}\n"
            f"Ordered By: {delivery_info.user.username}\n"
            f"Delivery Location: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
            f"Total: K{payment_history.total if payment_history else cart.total():.2f}"
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to generate QR code for delivery {delivery_id}: {str(e)}")
        messages.error(request, "Unable to generate QR code due to an error.")

    if request.method == 'POST' and delivery_info.delivery_status == 'in_progress':
        try:
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

            # Calculate total before deleting items
            total_amount = cart.total() if cart else 0.00

            cart.cartitem_set.all().delete()
            for key in ['mobile_order_data', 'mobile_transaction_id', 'stripe_session_id', 'paypal_order_data', 'pesapal_order_data', 'stripe_order_data', 'pesapal_order_id', 'pending_order']:
                request.session.pop(key, None)

            sms_body = (
                f"Order #{payment_history.id if payment_history else delivery_info.id} Confirmed!\n"
                f"Total: K{total_amount:.2f}\n"
                f"Delivery to: {delivery_info.address or delivery_info.get_predefined_address_display()}\n"
                f"Thank you for ordering with us!"
            )
            send_sms(delivery_info.phone_number, sms_body)

            messages.success(request, f"Order confirmed! SMS sent to {delivery_info.phone_number}")
            logger.info(f"Delivery {delivery_id} confirmed by user {request.user.username}")

            return redirect('payments:payment_success', delivery_id=delivery_id)

        except Exception as e:
            logger.error(f"Error confirming delivery {delivery_id}: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")

    context = {
        'delivery_info': delivery_info,
        'cart': cart,
        'payment_history': payment_history,
        'qr_image': qr_image_base64,  # Pass the base64-encoded QR code image or None if failed
    }
    return render(request, 'payments/success.html', context)

@login_required
@csrf_exempt
def payment_done(request):
    logger.debug(f"payment_done called: session_keys={list(request.session.keys())}, "
                 f"session_id={request.session.session_key}, "
                 f"referer={request.META.get('HTTP_REFERER', 'None')}")

    # Handle PayPal (unchanged)
    paypal_order_data = request.session.get('paypal_order_data')
    if paypal_order_data:
        try:
            cart = Cart.objects.get(id=paypal_order_data['cart_id'], user=request.user)
            delivery_info = create_delivery_info(request, paypal_order_data, cart)

            # Create PaymentHistory to make order visible to staff
            items = [
                {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                for item in cart.cartitem_set.all()
            ]
            payment_history = PaymentHistory.objects.create(
                user=request.user,
                cart=cart,
                delivery_info=delivery_info,
                total=cart.total(),
                items=items,
                transaction_id=f"PAYPAL-PENDING-{str(uuid.uuid4())[:8]}"
            )
            delivery_info.delivery_status = 'pending'
            delivery_info.save()

            for key in ['paypal_order_data', 'pending_order']:
                request.session.pop(key, None)
            messages.success(request, "PayPal payment initiated. Awaiting confirmation.")
            return redirect('payments:payment_success', delivery_id=delivery_info.id)

        except Cart.DoesNotExist:
            logger.error(f"Cart {paypal_order_data['cart_id']} not found for PayPal payment")
            messages.error(request, "Invalid payment session: Cart not found.")
            return redirect('payments:checkout')
        except Exception as e:
            logger.error(f"PayPal payment processing failed: {str(e)}")
            messages.error(request, f"Payment processing failed: {str(e)}")
            return redirect('payments:checkout')

    # Handle Stripe
    stripe_session_id = request.session.get('stripe_session_id')
    stripe_order_data = request.session.get('stripe_order_data')
    # Fallback to query parameter if session data is missing
    if not (stripe_session_id and stripe_order_data):
        session_key = request.GET.get('session_key')
        if session_key and session_key == request.session.session_key:
            stripe_session_id = request.session.get('stripe_session_id')
            stripe_order_data = request.session.get('stripe_order_data')
            logger.debug(f"Stripe session restored via query param: session_id={stripe_session_id}, order_data={stripe_order_data}")
        else:
            logger.error(f"Stripe session missing: session_id={stripe_session_id}, order_data={stripe_order_data}, "
                         f"query_session_key={session_key}, current_session_key={request.session.session_key}")
            messages.error(request, "Invalid payment session.")
            return redirect('payments:checkout')

    if stripe_session_id and stripe_order_data:
        try:
            status = verify_stripe_payment(stripe_session_id)
            if status == 'paid':
                cart = Cart.objects.get(id=stripe_order_data['cart_id'], user=request.user)
                delivery_info = create_delivery_info(request, stripe_order_data, cart)

                items = [
                    {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                    for item in cart.cartitem_set.all()
                ]
                payment_history = PaymentHistory.objects.create(
                    user=request.user,
                    cart=cart,
                    delivery_info=delivery_info,
                    total=cart.total(),
                    items=items,
                    transaction_id=f"STRIPE-{str(uuid.uuid4())}"
                )
                delivery_info.delivery_status = 'pending'
                delivery_info.save()

                for key in ['stripe_session_id', 'stripe_order_data', 'pending_order']:
                    request.session.pop(key, None)
                messages.success(request, "Stripe payment successful!")
                return redirect('payments:payment_success', delivery_id=delivery_info.id)
            else:
                logger.warning(f"Stripe payment not completed: status={status}")
                messages.error(request, "Stripe payment was not completed.")
                return redirect('payments:checkout')
        except Cart.DoesNotExist:
            logger.error(f"Cart {stripe_order_data['cart_id']} not found for Stripe payment")
            messages.error(request, "Invalid payment session: Cart not found.")
            return redirect('payments:checkout')
        except Exception as e:
            logger.error(f"Stripe payment verification failed: {str(e)}")
            messages.error(request, f"Payment verification failed: {str(e)}")
            return redirect('payments:checkout')

    # Handle Pesapal (unchanged)
    pesapal_order_data = request.session.get('pesapal_order_data')
    pesapal_order_id = request.session.get('pesapal_order_id')
    if pesapal_order_data and pesapal_order_id:
        try:
            status = verify_pesapal_payment(pesapal_order_id)
            if status == 'paid':
                cart = Cart.objects.get(id=pesapal_order_data['cart_id'], user=request.user)
                delivery_info = create_delivery_info(request, pesapal_order_data, cart)

                items = [
                    {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                    for item in cart.cartitem_set.all()
                ]
                payment_history = PaymentHistory.objects.create(
                    user=request.user,
                    cart=cart,
                    delivery_info=delivery_info,
                    total=cart.total(),
                    items=items,
                    transaction_id=f"PESAPAL-{pesapal_order_id}"
                )
                delivery_info.delivery_status = 'pending'
                delivery_info.save()

                for key in ['pesapal_order_data', 'pesapal_order_id', 'pending_order']:
                    request.session.pop(key, None)
                messages.success(request, "Pesapal payment successful!")
                return redirect('payments:payment_success', delivery_id=delivery_info.id)
            else:
                messages.error(request, "Pesapal payment was not completed.")
                return redirect('payments:checkout')
        except Cart.DoesNotExist:
            logger.error(f"Cart {pesapal_order_data['cart_id']} not found for Pesapal payment")
            messages.error(request, "Invalid payment session: Cart not found.")
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
    for key in ['paypal_order_data', 'stripe_session_id', 'stripe_order_data', 'pesapal_order_data', 'pesapal_order_id', 'mobile_order_data', 'mobile_transaction_id', 'pending_order']:
        request.session.pop(key, None)
    messages.error(request, "Payment was cancelled.")
    return redirect('payments:checkout')

@login_required
def order_history(request):
    """Display the user's order history."""
    history = PaymentHistory.objects.filter(user=request.user)
    return render(request, 'payments/order_history.html', {'history': history})

@login_required
def reorder(request, payment_id):
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
    """
    Display in-progress and cancelled orders for the logged-in customer.
    Cancelled orders are shown as 'Declined' with decline reason from Notification.
    Handles deletion of declined orders.
    """
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
                        DeliveryInfo,
                        id=delivery_id,
                        user=request.user,
                        delivery_status='in_progress'
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
                        DeliveryInfo,
                        id=delete_delivery_id,
                        user=request.user,
                        delivery_status='cancelled'
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
    logger.debug(f"In-progress orders context: {context}")
    return render(request, 'payments/in_progress_orders.html', context)