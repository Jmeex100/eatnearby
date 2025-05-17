from django.urls import path
from . import views
from . import user_views
from . import products_views
from . import revenue
from . import category_views
from . import delivery_views
from . import cart_views
from . import payment_views
from . import staff_views
from . import notification_views

app_name = 'superadmin'

urlpatterns = [
    # General Views
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.system_settings, name='system_settings'),

  # User Management
path('users/', user_views.user_list, name='user_list'),
path('user/<int:pk>/', user_views.UserDetailView.as_view(), name='user_detail'),
path('users/create/', user_views.user_create, name='user_create'),
path('users/<int:pk>/update/', user_views.user_update, name='user_update'),
path('users/<int:pk>/delete/', user_views.user_delete, name='user_delete'),
path('staff/', user_views.staff_list, name='staff_list'),
path('customers/', user_views.customer_list, name='customer_list'),
    # Product Management
    path('products/', products_views.product_list, name='product_list'),
    path('product/<int:pk>/', products_views.product_detail, name='product_detail'),
    path('products/create/', products_views.product_create, name='product_create'),
    path('products/<int:pk>/update/', products_views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', products_views.product_delete, name='product_delete'),

    # Revenue Management
    path('revenue/', revenue.revenue_dashboard, name='revenue_dashboard'),
    path('revenue/<str:method>/', revenue.revenue_detail, name='revenue_detail'),

    # Category Management
    path('categories/', category_views.category_list, name='category_list'),
    path('categories/create/', category_views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', category_views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', category_views.category_delete, name='category_delete'),

    # Delivery Management
    path('deliveries/', delivery_views.delivery_list, name='delivery_list'),
    path('delivery/<int:pk>/', delivery_views.delivery_detail, name='delivery_detail'),
    path('all-deliveries/', delivery_views.all_deliveries, name='all_deliveries'),

    # Cart Management
    path('carts/', cart_views.cart_list, name='cart_list'),
    path('cart/<int:pk>/', cart_views.cart_detail, name='cart_detail'),

    # Payment Management
    path('payments/', payment_views.payment_list, name='payment_list'),
    path('payment/<int:pk>/', payment_views.payment_detail, name='payment_detail'),

    # Staff Management
    path('staff-service-areas/', staff_views.staff_service_area_list, name='staff_service_area_list'),
    path('staff-service-area/<int:pk>/', staff_views.staff_service_area_detail, name='staff_service_area_detail'),
    path('staff-assignments/', staff_views.staff_assignment_list, name='staff_assignment_list'),
    path('staff-assignment/<int:pk>/', staff_views.staff_assignment_detail, name='staff_assignment_detail'),

    # Notification Management
    path('notifications/', notification_views.notification_list, name='notification_list'),
    path('notification/<int:pk>/', notification_views.notification_detail, name='notification_detail'),
]