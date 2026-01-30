# Location: .\apps\payments\stripe\client.py
# ==================== apps/payments/stripe/client.py ====================
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(amount: float, payment_id: str, metadata: dict = None):
    """Create Stripe payment intent."""
    
    # Convert to cents (XAF doesn't use decimal)
    amount_cents = int(amount)
    
    intent_metadata = {
        'payment_id': str(payment_id),
    }
    
    if metadata:
        intent_metadata.update(metadata)
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='xaf',  # Central African CFA Franc
            metadata=intent_metadata,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        
        return {
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")

