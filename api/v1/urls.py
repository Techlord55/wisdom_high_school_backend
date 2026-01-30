# Location: .\api\v1\urls.py
# ==================== api/v1/urls.py ====================
from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.auth.urls')),
    path('', include('api.v1.router')),
]