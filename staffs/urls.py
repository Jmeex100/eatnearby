from django.urls import path
from . import views

app_name = 'staffs'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('my-deliveries/', views.my_deliveries, name='my_deliveries'),
    path('delivery-history/', views.delivery_history, name='delivery_history'),
    path('accept-delivery/<int:delivery_id>/', views.accept_delivery, name='accept_delivery'),
    path('decline-delivery/<int:delivery_id>/', views.decline_delivery, name='decline_delivery'),
    path('availability/<int:staff_id>/', views.availability, name='staff_availability_single'),
    path('availability/', views.availability, name='staff_availability_all'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('delete-notification/<int:notification_id>/', views.delete_notification, name='delete_notification'),
]