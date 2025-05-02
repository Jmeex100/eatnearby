from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-done/', views.payment_done, name='payment_done'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('order-history/', views.order_history, name='order_history'),
    path('reorder/<int:payment_id>/', views.reorder, name='reorder'),
]