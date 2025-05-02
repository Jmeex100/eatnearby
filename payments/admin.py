
from django.contrib import admin
from .models import DeliveryInfo, PaymentHistory

admin.site.register(DeliveryInfo)
admin.site.register(PaymentHistory)