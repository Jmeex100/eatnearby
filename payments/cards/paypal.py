from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
import uuid
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

def initiate_paypal_payment(request, cart, delivery_info, total_usd):
    """
    Initiate a PayPal payment for the given cart.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order (None if not created).
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
        "amount": f"{total_usd:.2f}",
        "item_name": f"Order for {request.user.username}",
        "invoice": f"EATNEARBY-{uuid.uuid4().hex[:6]}",
        "currency_code": "USD",
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return_url": request.build_absolute_uri(reverse('payments:payment_done')),
        "cancel_return": request.build_absolute_uri(reverse('payments:payment_cancelled')),
        "custom": 'pending' if delivery_info is None else str(delivery_info.id),
    }

    # Enable sandbox mode if PAYPAL_TEST is True
    if getattr(settings, 'PAYPAL_TEST', True):
        paypal_dict["test_ipn"] = "1"

    form = PayPalPaymentsForm(initial=paypal_dict, button_type='buy')
    return form