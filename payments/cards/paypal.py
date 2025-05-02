from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
import uuid
from django.core.exceptions import ImproperlyConfigured

def initiate_paypal_payment(request, cart, delivery_info, total_usd):
    """
    Initiate a PayPal payment for the given cart and delivery info.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order.
        total_usd: The total amount in USD (float).

    Returns:
        PayPalPaymentsForm: A configured PayPal form ready to render.

    Raises:
        ImproperlyConfigured: If required PayPal settings are missing.
    """
    # Validate required settings
    if not hasattr(settings, 'PAYPAL_RECEIVER_EMAIL'):
        raise ImproperlyConfigured("PAYPAL_RECEIVER_EMAIL must be set in settings.py")

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{total_usd:.2f}",  # Ensure 2 decimal places
        "item_name": f"Order for {request.user.username}",
        "invoice": str(uuid.uuid4()),
        "currency_code": "USD",
        "notify_url": request.build_absolute_uri('/paypal/'),
        "return_url": request.build_absolute_uri('/payments/payment-done/'),
        "cancel_return": request.build_absolute_uri('/payments/payment-cancelled/'),
        "custom": str(delivery_info.id),  # Pass delivery_info ID for IPN
    }

    # Optional PayPal settings from settings.py
    if hasattr(settings, 'PAYPAL_TEST') and settings.PAYPAL_TEST:
        paypal_dict["test_ipn"] = "1"  # Enable sandbox mode if PAYPAL_TEST is True

    form = PayPalPaymentsForm(initial=paypal_dict)
    return form

def verify_paypal_payment(request):
    """
    Placeholder for verifying PayPal payment (e.g., via IPN).
    To be implemented if needed for custom IPN handling.
    """
    # Add logic here if you want custom IPN processing beyond django-paypal's default
    pass