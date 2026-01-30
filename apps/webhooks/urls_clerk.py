# ==================== apps/webhooks/urls_clerk.py ====================
from django.urls import path
from apps.webhooks.views import clerk_webhook

urlpatterns = [
    path('', clerk_webhook, name='clerk-webhook'),
]