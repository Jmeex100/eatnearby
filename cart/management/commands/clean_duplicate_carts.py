from django.core.management.base import BaseCommand
from django.db.models import Count
from cart.models import Cart, CartItem
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleans up duplicate carts by keeping the most recent one and merging cart items.'

    def handle(self, *args, **kwargs):
        # Find users with multiple carts
        duplicate_users = (
            Cart.objects.values('user')
            .annotate(cart_count=Count('id'))
            .filter(cart_count__gt=1)
        )

        for entry in duplicate_users:
            user_id = entry['user']
            cart_count = entry['cart_count']
            self.stdout.write(f"Processing user {user_id} with {cart_count} carts")

            # Get all carts for the user, ordered by most recent
            carts = Cart.objects.filter(user_id=user_id).order_by('-created_at')
            main_cart = carts[0]  # Keep the most recent cart
            duplicate_carts = carts[1:]  # Other carts to merge/delete

            for cart in duplicate_carts:
                # Move cart items to the main cart
                for item in cart.cartitem_set.all():
                    # Check if the same product exists in the main cart
                    existing_item = main_cart.cartitem_set.filter(
                        fast_food=item.fast_food,
                        food=item.food,
                        drink=item.drink,
                        quality=item.quality
                    ).first()

                    if existing_item:
                        # Merge quantities
                        existing_item.quantity += item.quantity
                        existing_item.save()
                    else:
                        # Reassign item to main cart
                        item.cart = main_cart
                        item.save()

                # Delete the duplicate cart
                cart.delete()

            self.stdout.write(f"Consolidated {cart_count} carts into one for user {user_id}")

        self.stdout.write(self.style.SUCCESS("Duplicate cart cleanup completed!"))