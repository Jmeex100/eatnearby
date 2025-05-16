from django.db import models
from auths.models import User
from payments.models import DeliveryInfo

class StaffServiceArea(models.Model):
    """
    Maps staff members to the predefined delivery points they can serve.
    """
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'staff'},
        related_name='service_areas'
    )
    point = models.CharField(
        max_length=30,
        choices=DeliveryInfo.DELIVERY_POINTS,
        help_text="Which delivery point this staff covers"
    )

    class Meta:
        unique_together = ('staff', 'point')
        verbose_name = "Staff Service Area"
        verbose_name_plural = "Staff Service Areas"

    def __str__(self):
        return f"{self.staff.username} covers {self.get_point_display()}"

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
        ('delivery_declined', 'Delivery Declined'),
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