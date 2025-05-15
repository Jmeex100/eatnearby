import uuid
import logging

logger = logging.getLogger(__name__)

def initiate_airtel_payment(request, cart, delivery_info, total_zmw):
    """
    Initiate a simulated Airtel Money payment.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order (None if not created).
        total_zmw: The total amount in ZMW (float).

    Returns:
        dict: Contains 'status', 'message', and 'transaction_id'.

    Raises:
        Exception: If payment initiation fails.
    """
    try:
        # Get phone number from session if delivery_info is None
        phone_number = (delivery_info.phone_number if delivery_info else
                       request.session.get('pending_order', {}).get('phone_number'))
        if not phone_number:
            raise Exception("Phone number is required for Airtel payment")

        # Simulate Airtel payment initiation
        transaction_id = str(uuid.uuid4())
        logger.info(f"Simulated Airtel payment initiated for {phone_number}, Amount: {total_zmw} ZMW, Transaction ID: {transaction_id}")

        return {
            'status': 'success',
            'message': f'Airtel payment of K{total_zmw:.2f} initiated. Please confirm on your phone {phone_number}.',
            'transaction_id': transaction_id,
        }
    except Exception as e:
        logger.error(f"Simulated Airtel payment initiation failed: {str(e)}")
        raise Exception(f"Simulated Airtel payment initiation failed: {str(e)}")