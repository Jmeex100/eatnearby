import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging
import urllib3

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY
# Disable proxy to avoid ProxyError
stripe.proxy = None
urllib3.util.connection.ALLOWED_HOSTNAMES = ['api.stripe.com']

def initiate_stripe_payment(request, cart, delivery_info, total_usd):
    """
    Initiate a Stripe Checkout session for the given cart.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order (None if not created).
        total_usd: The total amount in USD (float).

    Returns:
        dict: Contains 'checkout_url', 'session_id', 'public_key', 'cart', and 'total_usd'.

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
        product = item.get_product()
        if not product:
            logger.error(f"No product found for cart item {item.id}")
            raise Exception(f"Invalid product in cart item {item.id}")
        unit_amount = int((float(item.subtotal()) / item.quantity / 28.638) * 100)  # Convert ZMW to USD cents
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': unit_amount,
                'product_data': {
                    'name': product.name,
                },
            },
            'quantity': item.quantity,
        })

    # Ensure session_key is initialized
    if not request.session.session_key:
        request.session.save()

    # Create Stripe Checkout session
    try:
        success_url = request.build_absolute_uri('/payments/payment-done/') + f'?session_key={request.session.session_key}'
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=request.build_absolute_uri('/payments/payment-cancelled/'),
            customer_email=request.user.email or "customer@example.com",
            metadata={
                'cart_id': str(cart.id),
                'delivery_info_id': 'pending' if delivery_info is None else str(delivery_info.id),
                'session_key': request.session.session_key,
            }
        )
        logger.debug(f"Stripe Checkout session created: {session.id}, URL: {session.url}")
        return {
            'checkout_url': session.url,
            'session_id': session.id,
            'public_key': settings.STRIPE_PUBLISHABLE_KEY,
            'cart': cart,
            'total_usd': total_usd,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}", exc_info=True)
        raise Exception(f"Stripe payment failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating Stripe session: {str(e)}", exc_info=True)
        raise Exception(f"Stripe payment failed: {str(e)}")

def verify_stripe_payment(session_id):
    """
    Verify the Stripe payment status using the session ID.

    Args:
        session_id: The Stripe Checkout session ID.

    Returns:
        str: Payment status (e.g., 'paid', 'unpaid').s

    Raises:
        Exception: If verification fails.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        logger.debug(f"Stripe session status: {session.payment_status}")
        return session.payment_status
    except stripe.error.StripeError as e:
        logger.error(f"Stripe verification error: {str(e)}", exc_info=True)
        raise Exception(f"Stripe verification failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error verifying Stripe session: {str(e)}", exc_info=True)
        raise Exception(f"Stripe verification failed: {str(e)}")