# ==================== apps/webhooks/urls_stripe.py ====================
from django.urls import path
from apps.webhooks.views import stripe_webhook

urlpatterns = [
    path('', stripe_webhook, name='stripe-webhook'),
]