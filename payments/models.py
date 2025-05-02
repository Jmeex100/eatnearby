from django.db import models
from auths.models import User
from cart.models import Cart

class DeliveryInfo(models.Model):
    id = models.BigAutoField(primary_key=True)

    DELIVERY_POINTS = [
        ('evelyhone', 'Evelyn Hone College'),
        ('zambia_police', 'Zambia Police Headquarters'),
        ('zambia_accountancy', 'Zambia Centre for Accountancy'),
        ('mukuba_house', 'Mukuba Pension House'),
        ('bus_terminus', 'Lusaka Intercity Bus Terminus'),
        ('national_museum', 'Lusaka National Museum'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Card'),
    ]

    MOBILE_MONEY_PROVIDERS = [
        ('airtel', 'Airtel'),
        ('mtn', 'MTN'),
        ('zamtel', 'Zamtel'),
    ]

    CARD_PROVIDERS = [
        ('paypal', 'Paypal'),
        ('pesapal', 'Pesapal'),
        ('stripe', 'Stripe'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)

    address = models.CharField(max_length=100, blank=True, null=True)
    predefined_address = models.CharField(
        max_length=30,
        choices=DELIVERY_POINTS,
        blank=True,
        null=True,
        help_text="Predefined delivery point"
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending',
        help_text="Current delivery status"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash',
        help_text="Payment method used"
    )
    payment_provider = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Specific provider for Mobile Money or Card (e.g., Airtel, Stripe)"
    )

    phone_number = models.CharField(max_length=20)
    secondary_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Optional secondary contact number"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.predefined_address and not self.address:
            self.address = self.get_predefined_address_display()
        super().save(*args, **kwargs)

    def __str__(self):
        address_display = self.address or self.get_predefined_address_display() or "N/A"
        return f"Delivery for {self.user.username} at {address_display}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Info"
        verbose_name_plural = "Delivery Info"


class PaymentHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True) #paypal transaction

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    delivery_info = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_histories'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    items = models.JSONField(
        help_text="List of items in the payment (e.g., [{'name': 'Pizza', 'quantity': 2, 'subtotal': 15.00}])"
    )

    def __str__(self):
        return f"Payment by {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment History"
        verbose_name_plural = "Payment Histories"