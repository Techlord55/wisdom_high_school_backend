"""
Django security utilities and helper functions.
"""
from django.core.management.utils import get_random_secret_key
import secrets
import string


def generate_secret_key():
    """
    Generate a secure Django SECRET_KEY.
    
    Usage:
        from apps.common.security import generate_secret_key
        print(generate_secret_key())
    """
    return get_random_secret_key()


def generate_api_key(length=32):
    """
    Generate a secure API key.
    
    Args:
        length (int): Length of the API key
        
    Returns:
        str: Secure random API key
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_webhook_secret(length=40):
    """
    Generate a secure webhook secret.
    
    Args:
        length (int): Length of the webhook secret
        
    Returns:
        str: Secure random webhook secret
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == '__main__':
    print("🔐 Security Key Generator")
    print("=" * 60)
    print(f"\nDjango SECRET_KEY:\n{generate_secret_key()}")
    print(f"\nAPI Key:\n{generate_api_key()}")
    print(f"\nWebhook Secret:\n{generate_webhook_secret()}")
    print("\n" + "=" * 60)
    print("⚠️  Store these securely in your .env file!")
    print("⚠️  NEVER commit these to version control!")
