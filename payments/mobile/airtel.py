import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def initiate_airtel_payment(request, cart, delivery_info, total_zmw):
    """
    Initiate an Airtel Money payment for the given cart and delivery info.

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
    # Validate required settings (replace with actual Airtel API credentials)
    if not hasattr(settings, 'AIRTEL_API_KEY') or not hasattr(settings, 'AIRTEL_API_SECRET'):
        raise ImproperlyConfigured("AIRTEL_API_KEY and AIRTEL_API_SECRET must be set in settings.py")

    try:
        # Placeholder: Simulate Airtel Money API call
        # In reality, you'd use requests.post() to an Airtel endpoint
        phone_number = delivery_info.phone_number
        logger.debug(f"Simulating Airtel payment for {phone_number}, Total: {total_zmw} ZMW")

        # Simulate success (replace with actual API logic)
        transaction_id = f"AT{delivery_info.id}{cart.id}"  # Dummy transaction ID
        logger.info(f"Airtel payment initiated: Transaction ID {transaction_id}")
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'message': f"Payment request sent to {phone_number}. Please confirm on your Airtel Money app."
        }
    except Exception as e:
        logger.error(f"Airtel payment failed: {str(e)}")
        raise Exception(f"Airtel payment initiation failed: {str(e)}")