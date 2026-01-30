# ==================== apps/webhooks/views.py ====================
import json
import hmac
import hashlib
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from apps.users import services as user_services
from apps.students import services as student_services
from apps.payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def verify_clerk_webhook(request):
    """Verify Clerk webhook signature."""
    signature = request.headers.get('svix-signature')
    timestamp = request.headers.get('svix-timestamp')
    svix_id = request.headers.get('svix-id')
    
    if not all([signature, timestamp, svix_id]):
        return False
    
    # Construct the signed content
    signed_content = f"{svix_id}.{timestamp}.{request.body.decode()}"
    
    # Create signature
    expected_signature = hmac.new(
        settings.CLERK_WEBHOOK_SECRET.encode(),
        signed_content.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(f"v1,{expected_signature}", signature.split(',')[1])


@csrf_exempt
@require_POST
def clerk_webhook(request):
    """Handle Clerk webhooks."""
    
    # Verify signature
    if not verify_clerk_webhook(request):
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    try:
        data = json.loads(request.body)
        event_type = data.get('type')
        event_data = data.get('data')
        
        if event_type == 'user.created':
            # Create user
            user = user_services.create_user_from_clerk(event_data)
            
            # Create student profile by default
            student_services.create_student_profile(
                user=user,
                class_level='Form 1',
                section='grammar'
            )
        
        elif event_type == 'user.updated':
            # Update user
            user_services.update_user_from_clerk(event_data)
        
        elif event_type == 'user.deleted':
            # Delete user
            clerk_id = event_data.get('id')
            user_services.delete_user_by_clerk_id(clerk_id)
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Get payment from metadata
        payment_id = payment_intent.get('metadata', {}).get('payment_id')
        
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.payment_status = 'completed'
                payment.stripe_payment_intent_id = payment_intent['id']
                payment.transaction_id = payment_intent['id']
                payment.paid_at = timezone.now()
                payment.save()
                
                # TODO: Send confirmation email
                
            except Payment.DoesNotExist:
                pass
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        # Handle failed payment
        print(f"Payment failed: {payment_intent['id']}")
    
    return JsonResponse({'status': 'success'})



# ==================== apps/webhooks/urls_stripe.py ====================
from django.urls import path
from apps.webhooks.views import stripe_webhook

urlpatterns = [
    path('', stripe_webhook, name='stripe-webhook'),
]