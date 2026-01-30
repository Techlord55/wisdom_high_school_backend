# Location: .\config\urls.py
# ==================== config/urls.py ====================
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Health Check
    path('api/health/', include('api.health')),
    
    # API v1
    path('api/v1/', include('api.v1.urls')),
    
    # Webhooks

    path('webhooks/clerk/', include('apps.webhooks.urls_clerk')),
    path('webhooks/stripe/', include('apps.webhooks.urls_stripe')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
