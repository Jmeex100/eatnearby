from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from .models import DeliveryInfo, PaymentHistory
from cart.models import Cart

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == 'Completed':
        delivery_id = ipn_obj.custom  # DeliveryInfo ID passed in 'custom'
        try:
            delivery_info = DeliveryInfo.objects.get(id=delivery_id)
            cart = delivery_info.cart

            items = [
                {"name": item.get_product().name, "quantity": item.quantity, "subtotal": float(item.subtotal())}
                for item in cart.cartitem_set.all()
            ]
            payment_history = PaymentHistory(
                user=delivery_info.user,
                cart=cart,
                delivery_info=delivery_info,
                total=cart.total(),
                items=items,
                transaction_id=ipn_obj.txn_id
            )
            payment_history.save()

            delivery_info.delivery_status = 'completed'
            delivery_info.save()
            cart.cartitem_set.all().delete()
        except DeliveryInfo.DoesNotExist:
            # Log error or notify admin if needed
            pass