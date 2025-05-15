import logging
import uuid
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def initiate_mtn_payment(request, cart, delivery_info, total_zmw, phone_number):
    """
    Simulate an MTN MoMo payment for the given cart and delivery info.
    """
    if not hasattr(settings, 'MTN_SUBSCRIPTION_KEY') or not hasattr(settings, 'MTN_CALLBACK_HOST'):
        raise ImproperlyConfigured("MTN_SUBSCRIPTION_KEY and MTN_CALLBACK_HOST must be set in settings.py")

    try:
        # Use provided phone_number, fallback to session
        phone = phone_number or request.session.get('pending_order', {}).get('phone_number')
        if not phone:
            raise Exception("Phone number is required for MTN payment")

        # Generate transaction_id without delivery_info.id if None
        transaction_id = f"MTN-{(delivery_info.id if delivery_info else 'PENDING')}-{cart.id}"
        logger.info(f" MTN payment for {phone}, Total: {total_zmw} ZMW, Transaction ID: {transaction_id}")
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'message': f" payment request sent to {phone}. Please confirm on your MTN MoMo app."
        }
    except Exception as e:
        logger.error(f" MTN payment failed: {str(e)}")
        raise Exception(f" MTN payment initiation failed: {str(e)}")

def check_mtn_payment_status(transaction_id):
    """
    Simulate checking the status of an MTN MoMo payment.
    """
    logger.info(f" MTN transaction {transaction_id} status check: SUCCESSFUL")
    return {
        'status': 'SUCCESSFUL',
        'details': {'transaction_id': transaction_id, 'message': ' payment completed'}
    }