# Location: .\apps\users\middleware.py
import time
from django.core.cache import cache
from django.http import JsonResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only rate limit API requests
        if request.path.startswith('/api/'):
            user_ip = self.get_client_ip(request)
            cache_key = f"rl_{user_ip}"
            requests = cache.get(cache_key, 0)

            if requests >= 100:  # Limit to 100 requests per minute
                return JsonResponse(
                    {"error": "Rate limit exceeded. Try again later."}, 
                    status=429
                )
            
            cache.set(cache_key, requests + 1, timeout=60)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    