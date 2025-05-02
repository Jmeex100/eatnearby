import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def initiate_zamtel_payment(request, cart, delivery_info, total_zmw):
    """
    Initiate a Zamtel Mobile Money payment for the given cart and delivery info.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order.
        total_zmw: The total amount in ZMW (Zambian Kwacha).

    Returns:
        dict: Contains 'status' and 'message' or 'transaction_id' if successful.

    Raises:
        Exception: If payment initiation fails.
    """
    # Validate required settings (replace with actual Zamtel API credentials)
    if not hasattr(settings, 'ZAMTEL_API_KEY') or not hasattr(settings, 'ZAMTEL_API_SECRET'):
        raise ImproperlyConfigured("ZAMTEL_API_KEY and ZAMTEL_API_SECRET must be set in settings.py")

    try:
        # Placeholder: Simulate Zamtel Mobile Money API call
        phone_number = delivery_info.phone_number
        logger.debug(f"Simulating Zamtel payment for {phone_number}, Total: {total_zmw} ZMW")

        # Simulate success (replace with actual API logic)
        transaction_id = f"ZT{delivery_info.id}{cart.id}"  # Dummy transaction ID
        logger.info(f"Zamtel payment initiated: Transaction ID {transaction_id}")
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'message': f"Payment request sent to {phone_number}. Please confirm on your Zamtel Mobile Money app or dial *344#."
        }
    except Exception as e:
        logger.error(f"Zamtel payment failed: {str(e)}")
        raise Exception(f"Zamtel payment initiation failed: {str(e)}")