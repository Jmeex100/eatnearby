from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from .models import DeliveryInfo, PaymentHistory
from cart.models import Cart
import logging

logger = logging.getLogger(__name__)

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender
    logger.info(f"PayPal IPN received: payment_status={ipn_obj.payment_status}, delivery_id={ipn_obj.custom}, txn_id={ipn_obj.txn_id}")
    
    if ipn_obj.payment_status == 'Completed':
        delivery_id = ipn_obj.custom
        try:
            delivery_info = DeliveryInfo.objects.get(id=delivery_id)
            # Check for existing PaymentHistory
            payment_history = PaymentHistory.objects.filter(delivery_info=delivery_info).first()
            if payment_history:
                if payment_history.transaction_id.startswith('PAYPAL-PENDING-'):
                    # Update existing PaymentHistory
                    payment_history.transaction_id = ipn_obj.txn_id
                    payment_history.save()
                    logger.info(f"Updated PayPal PaymentHistory for delivery {delivery_id}, transaction {ipn_obj.txn_id}")
                else:
                    logger.info(f"PaymentHistory already exists for delivery {delivery_id}, transaction {payment_history.transaction_id}")
                return

            # Fallback: Create new PaymentHistory
            cart = delivery_info.cart
            items = [
                {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                for item in cart.cartitem_set.all()
            ]
            payment_history = PaymentHistory.objects.create(
                user=delivery_info.user,
                cart=cart,
                delivery_info=delivery_info,
                total=cart.total(),
                items=items,
                transaction_id=ipn_obj.txn_id
            )
            logger.info(f"Created PayPal PaymentHistory for delivery {delivery_id}, transaction {ipn_obj.txn_id}")
        except DeliveryInfo.DoesNotExist:
            logger.error(f"PayPal IPN failed: DeliveryInfo {delivery_id} not found")
        except Exception as e:
            logger.error(f"PayPal IPN processing error for delivery {delivery_id}: {str(e)}")
    else:
        logger.warning(f"PayPal IPN ignored: payment_status={ipn_obj.payment_status}, delivery_id={ipn_obj.custom}")