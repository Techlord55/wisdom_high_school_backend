# Location: .\apps\settings\urls.py
# ==================== apps/settings/urls.py ====================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.settings.views import SystemSettingsViewSet

router = DefaultRouter()
router.register(r'settings', SystemSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]
