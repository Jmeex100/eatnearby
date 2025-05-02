# auths/urls.py
from django.urls import path
from .views import auth_views, product_views, profile_views, misc_views

urlpatterns = [
    # Auth
    path('login/', auth_views.login_page, name='login'),
    path('register/', auth_views.register_page, name='register'),
    path('logout/', auth_views.logout_page, name='logout'),

    # Products
    path('orders/', product_views.orders, name='orders'),
    path('order/<str:item_id>/<str:category>/', product_views.order, name='order'),
    path('products/', product_views.products, name='products'),

    # Profile
    path('profile/', profile_views.profile, name='profile'),
    path('settings/', profile_views.settings, name='settings'),

    # Misc
    path('index', misc_views.index, name='index'),
    path('help/', misc_views.help_page, name='help'),
]