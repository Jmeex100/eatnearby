import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def initiate_stripe_payment(request, cart, delivery_info, total_usd):
    """
    Initiate a Stripe Checkout session for the given cart and delivery info.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order.
        total_usd: The total amount in USD (float).

    Returns:
        dict: Contains 'checkout_url' for redirecting to Stripe's hosted payment page.

    Raises:
        ImproperlyConfigured: If required Stripe settings are missing.
        Exception: If Stripe API call fails.
    """
    # Validate required settings
    required_settings = ['STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY']
    for setting in required_settings:
        if not hasattr(settings, setting):
            raise ImproperlyConfigured(f"{setting} must be set in settings.py")

    # Prepare line items from cart
    line_items = []
    for item in cart.cartitem_set.all():
        product = item.get_product()  # Call the method with ()
        if not product:
            logger.error(f"No product found for cart item {item.id}")
            raise Exception(f"Invalid product in cart item {item.id}")
        unit_amount = int((float(item.subtotal()) / item.quantity / 28.638) * 100)  # Convert ZMW to USD cents
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': unit_amount,
                'product_data': {
                    'name': product.name,  # Now product is an object with a 'name' attribute
                },
            },
            'quantity': item.quantity,
        })

    # Ensure total matches (in cents)
    total_usd_cents = int(total_usd * 100)

    # Create Stripe Checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payments/payment-done/'),
            cancel_url=request.build_absolute_uri('/payments/payment-cancelled/'),
            customer_email=request.user.email or "customer@example.com",
            metadata={
                'cart_id': str(cart.id),
                'delivery_info_id': str(delivery_info.id),
            }
        )
        logger.debug(f"Stripe Checkout session created: {session.id}, URL: {session.url}")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}")
        raise Exception(f"Stripe payment failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating Stripe session: {str(e)}")
        raise Exception(f"Stripe payment failed: {str(e)}")

    return {
        'checkout_url': session.url,
        'session_id': session.id
    }

def verify_stripe_payment(session_id):
    """
    Verify the Stripe payment status using the session ID.

    Args:
        session_id: The Stripe Checkout session ID.

    Returns:
        str: Payment status (e.g., 'paid', 'unpaid').

    Raises:
        Exception: If verification fails.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        logger.debug(f"Stripe session status: {session.payment_status}")
        return session.payment_status
    except stripe.error.StripeError as e:
        logger.error(f"Stripe verification error: {str(e)}")
        raise Exception(f"Stripe verification failed: {str(e)}")