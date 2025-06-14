from django.db import models
from django.core.validators import RegexValidator
import logging
from auths.models import User
from cart.models import Cart

logger = logging.getLogger(__name__)

class DeliveryInfo(models.Model):
    """Model to store delivery information for an order."""
    id = models.BigAutoField(primary_key=True)

    DELIVERY_POINTS = [
        ('evelynhone', 'Evelyn Hone College'),
        ('zambia_police', 'Zambia Police Headquarters'),
        ('zambia_accountancy', 'Zambia Centre for Accountancy'),
        ('mukuba_house', 'Mukuba Pension House'),
        ('bus_terminus', 'Lusaka Intercity Bus Terminus'),
        ('national_museum', 'Lusaka National Museum'),
    ]

    DELIVERY_POINTS_COORDS = {
        "evelynhone": {"lat": -15.4163, "lng": 28.2993},  # Evelyn Hone College
        "zambia_police": {"lat": -15.4211, "lng": 28.3014},  # Zambia Police Headquarters
        "zambia_accountancy": {"lat": -15.4163, "lng": 28.2888},  # Zambia Centre for Accountancy
        "mukuba_house": {"lat": -15.4182, "lng": 28.2845},  # Mukuba Pension House
        "bus_terminus": {"lat": -15.4204, "lng": 28.2902},  # Lusaka Intercity Bus Terminus
        "national_museum": {"lat": -15.4198, "lng": 28.2877},  # Lusaka National Museum
    }

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

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who placed the order"
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        help_text="Cart containing order items"
    )
    address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Custom delivery address, if not using predefined point"
    )
    predefined_address = models.CharField(
        max_length=30,
        choices=DELIVERY_POINTS,
        blank=True,
        null=True,
        help_text="Predefined delivery point"
    )
    is_pos_order = models.BooleanField(
        default=False,
        help_text="Indicates if this is an in-store POS order"
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
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+\d{10,15}$', 'Enter a valid phone number (e.g., +260973546375)')],
        help_text="Primary contact number"
    )
    secondary_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+\d{10,15}$', 'Enter a valid phone number (e.g., +260973546375)')],
        help_text="Optional secondary contact number"
    )
    restaurant_location = models.JSONField(
        null=True,
        blank=True,
        help_text="Restaurant coordinates {'lat': float, 'lng': float}"
    )
    driver_location = models.JSONField(
        null=True,
        blank=True,
        help_text="Driver coordinates {'lat': float, 'lng': float}"
    )
    last_location_update = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of last location update"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_predefined_address_display(self):
        """Return the display name of the predefined address."""
        return dict(self.DELIVERY_POINTS).get(self.predefined_address, self.predefined_address)

    def get_payment_method_display(self):
        """Return the display name of the payment method."""
        return dict(self.PAYMENT_METHODS).get(self.payment_method, self.payment_method)

    def save(self, *args, **kwargs):
        """Override save to set restaurant location and log status changes."""
        if self.pk:
            try:
                old_instance = DeliveryInfo.objects.get(pk=self.pk)
                if old_instance.delivery_status != self.delivery_status:
                    logger.info(
                        f"DeliveryInfo {self.id} status changed from "
                        f"{old_instance.delivery_status} to {self.delivery_status}"
                    )
            except DeliveryInfo.DoesNotExist:
                logger.warning(f"DeliveryInfo {self.id} not found during save")
        else:
            logger.info(f"New DeliveryInfo created with status {self.delivery_status}")

        # Always set restaurant_location to Zambia Centre for Accountancy
        self.restaurant_location = self.DELIVERY_POINTS_COORDS['zambia_accountancy']

        # Set address from predefined_address if not provided
        if self.predefined_address and not self.address:
            self.address = self.get_predefined_address_display()

        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the delivery."""
        address_display = self.address or self.get_predefined_address_display() or "N/A"
        return f"Delivery for {self.user.username} at {address_display}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Info"
        verbose_name_plural = "Delivery Info"

class PaymentHistory(models.Model):
    """Model to store payment history for an order."""
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction ID from payment provider (e.g., PayPal)"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who made the payment"
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Cart associated with the payment"
    )
    delivery_info = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_histories',
        help_text="Associated delivery information"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total payment amount"
    )
    items = models.JSONField(
        default=list,
        help_text="List of items in the payment (e.g., [{'name': 'Pizza', 'quantity': 2, 'subtotal': 15.00}])"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation of the payment."""
        return f"Payment by {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment History"
        verbose_name_plural = "Payment Histories"