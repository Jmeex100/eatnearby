from django.contrib import admin
from .models import DeliveryInfo, PaymentHistory

@admin.register(DeliveryInfo)
class DeliveryInfoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'predefined_address', 'delivery_status', 'payment_method',
        'phone_number', 'last_location_update', 'created_at'
    )
    list_filter = ('delivery_status', 'payment_method', 'predefined_address')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('last_location_update', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'cart')

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'delivery_info', 'total', 'created_at')
    list_filter = ('delivery_info__delivery_status', 'delivery_info__payment_method')
    search_fields = ('user__username', 'transaction_id')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'cart', 'delivery_info')