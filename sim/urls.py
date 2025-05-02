
from django.urls import path

from . import views
from auths import urls

urlpatterns = [
    path('', views.home, name='home'),
    path('map/', views.map, name='map'),
     path('menu/', views.menu, name='menu'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
 
    
]
