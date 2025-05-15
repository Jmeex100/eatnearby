import logging
import uuid
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def initiate_zamtel_payment(request, cart, delivery_info, total_zmw):
    """
    Simulate a Zamtel Money payment for the given cart and delivery info.
    """
    if not hasattr(settings, 'ZAMTEL_API_KEY') or not hasattr(settings, 'ZAMTEL_API_SECRET'):
        raise ImproperlyConfigured("ZAMTEL_API_KEY and ZAMTEL_API_SECRET must be set in settings.py")

    try:
        # Get phone number from session if delivery_info is None
        phone_number = (delivery_info.phone_number if delivery_info else
                       request.session.get('pending_order', {}).get('phone_number'))
        if not phone_number:
            raise Exception("Phone number is required for Zamtel payment")

        # Generate transaction_id without delivery_info.id if None
        transaction_id = f"ZT-{(delivery_info.id if delivery_info else 'PENDING')}-{cart.id}"
        logger.info(f"Simulated Zamtel payment for {phone_number}, Total: {total_zmw} ZMW, Transaction ID: {transaction_id}")
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'message': f"Simulated payment request sent to {phone_number}. Please confirm on your Zamtel Money app."
        }
    except Exception as e:
        logger.error(f"Simulated Zamtel payment failed: {str(e)}")
        raise Exception(f"Simulated Zamtel payment initiation failed: {str(e)}")