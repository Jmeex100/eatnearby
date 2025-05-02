from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sim.urls')),
    path('', include('auths.urls')),
    path('cart/', include('cart.urls')),
    path('payments/', include('payments.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),  # Matches /paypal/
    path('', include('pwa.urls')),  # Add PWA URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)