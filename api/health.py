# Location: .\api\health.py
# ==================== api/health.py ====================
from django.urls import path
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'scholarnode-backend'
    })


# ADD THIS - Django needs urlpatterns to include this module
urlpatterns = [
    path('', health_check, name='health-check'),
]