from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import DeliveryInfo
from .models import StaffAssignment, Notification

@receiver(post_save, sender=StaffAssignment)
def create_notification_on_assignment(sender, instance, created, **kwargs):
    """Create notification when a staff is assigned to a delivery."""
    if created:
        message = (
            f"You have been assigned to deliver order for {instance.delivery.user.username} "
            f"at {instance.delivery.address or instance.delivery.get_predefined_address_display()}."
        )
        Notification.objects.create(
            recipient=instance.staff,
            message=message,
            notification_type='new_order',
            related_delivery=instance.delivery
        )

@receiver(post_save, sender=DeliveryInfo)
def create_notification_on_status_change(sender, instance, **kwargs):
    """Create notifications for assigned staff when delivery status changes."""
    assignments = instance.staff_assignments.all()
    for assignment in assignments:
        if instance.delivery_status == 'in_progress':
            message = (
                f"Your assigned order for {instance.user.username} at "
                f"{instance.address or instance.get_predefined_address_display()} "
                f"is now in progress."
            )
            Notification.objects.create(
                recipient=assignment.staff,
                message=message,
                notification_type='delivery_almost_complete',
                related_delivery=instance
            )
        elif instance.delivery_status == 'completed':
            message = (
                f"Your assigned order for {instance.user.username} at "
                f"{instance.address or instance.get_predefined_address_display()} "
                f"has been completed."
            )
            Notification.objects.create(
                recipient=assignment.staff,
                message=message,
                notification_type='delivery_completed',
                related_delivery=instance
            )