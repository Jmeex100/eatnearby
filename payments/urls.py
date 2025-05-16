from django.urls import path
from . import views
from paypal.standard.ipn import views as paypal_views

app_name = 'payments'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('airtel-payment-process/', views.airtel_payment_process, name='airtel_payment_process'),
    path('zamtel-payment-process/', views.zamtel_payment_process, name='zamtel_payment_process'),
    path('mtn-payment-process/', views.mtn_payment_process, name='mtn_payment_process'),
    path('payment-success/<int:delivery_id>/', views.payment_success, name='payment_success'),
    path('payment-done/', views.payment_done, name='payment_done'),
    path('delivering/', views.in_progress_orders, name='in_progress_orders'),

    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('order-history/', views.order_history, name='order_history'),
    path('reorder/<int:payment_id>/', views.reorder, name='reorder'),
    path('mtn-callback/', views.mtn_callback, name='mtn_callback'),
    path('paypal/', paypal_views.ipn, name='paypal-ipn'),
]