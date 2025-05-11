from django.db import models
from auths.models import User
from payments.models import DeliveryInfo

class StaffAssignment(models.Model):
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='delivery_assignments'
    )
    delivery = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['staff', 'delivery']
        verbose_name = "Staff Assignment"
        verbose_name_plural = "Staff Assignments"

    def __str__(self):
        return f"{self.staff.username} assigned to Delivery {self.delivery.id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('delivery_almost_complete', 'Delivery Almost Complete'),
        ('delivery_completed', 'Delivery Completed'),
        ('alert', 'Alert'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='notifications'
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='new_order'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_delivery = models.ForeignKey(
        DeliveryInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"