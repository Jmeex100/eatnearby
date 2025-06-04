from django.db import models
from auths.models import User, FastFood, Food, Drink

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_cart')
        ]

    def total(self):
        return sum(item.subtotal() for item in self.cartitem_set.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    fast_food = models.ForeignKey(FastFood, null=True, blank=True, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, null=True, blank=True, on_delete=models.CASCADE)
    drink = models.ForeignKey(Drink, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    quality = models.CharField(max_length=50)

    def get_product(self):
        return self.fast_food or self.food or self.drink

    def subtotal(self):
        product = self.get_product()
        if not product:
            return 0
        return product.price * self.quantity

    def __str__(self):
        product = self.get_product()
        return f"{product.name} x{self.quantity}"