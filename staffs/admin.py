from django.contrib import admin
from .models import StaffAssignment, Notification

class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ('staff', 'delivery', 'assigned_at')
    list_filter = ('assigned_at', 'staff', 'delivery')
    search_fields = ('staff__username', 'delivery__id')
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at',)

    # Optional: Add filter for staff user type
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Filter the queryset to ensure only staff assignments are shown
        return queryset.filter(staff__user_type='staff')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'message', 'is_read', 'created_at', 'related_delivery')
    list_filter = ('notification_type', 'is_read', 'created_at', 'recipient')
    search_fields = ('recipient__username', 'message', 'related_delivery__id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    # Optional: Add filter for staff user type
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Filter the queryset to ensure only staff notifications are shown
        return queryset.filter(recipient__user_type='staff')

    # Optional: Inline display for related deliveries
    def related_delivery(self, obj):
        return obj.related_delivery.id if obj.related_delivery else None
    related_delivery.admin_order_field = 'related_delivery__id'

# Registering the models in Django admin
admin.site.register(StaffAssignment, StaffAssignmentAdmin)
admin.site.register(Notification, NotificationAdmin)
