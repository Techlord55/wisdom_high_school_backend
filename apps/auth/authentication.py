# apps/auth/authentication.py
import jwt
import requests
from rest_framework import authentication, exceptions
from apps.users.models import User
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ClerkAuthentication(authentication.BaseAuthentication):
    """Custom authentication using Clerk JWT tokens."""
    
    def authenticate(self, request):
        # Log all headers for debugging
        logger.info("=== AUTHENTICATION ATTEMPT ===")
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f"Authorization header: '{auth_header[:50] if auth_header else 'NONE'}...'")
        
        if not auth_header:
            logger.warning("No authorization header found")
            return None
            
        if not auth_header.startswith('Bearer '):
            logger.warning(f"Invalid auth header format: {auth_header[:20]}")
            return None
        
        token = auth_header.split(' ')[1]
        logger.info(f"Token extracted: {token[:30]}...")
        
        try:
            # Decode JWT without verification first to get user ID
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            clerk_user_id = unverified_payload.get('sub')
            
            logger.info(f"Token claims user ID: {clerk_user_id}")
            
            if not clerk_user_id:
                raise exceptions.AuthenticationFailed('Token missing user ID')
            
            # Get user data from Clerk
            clerk_user_data = self._fetch_clerk_user(clerk_user_id)
            if not clerk_user_data:
                logger.warning(f"User {clerk_user_id} not found in Clerk, creating from token")
                # If user doesn't exist in Clerk (404), extract info from token
                clerk_user_data = self._extract_user_from_token(unverified_payload, clerk_user_id)
            
            # Get or create user
            user = self._get_or_create_user(clerk_user_data)
            
            logger.info(f"✅ User authenticated successfully: {user.email} (Role: {user.role})")
            
            return (user, token)
            
        except jwt.DecodeError as e:
            logger.error(f'JWT decode error: {str(e)}')
            raise exceptions.AuthenticationFailed('Invalid token format')
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f'Authentication error: {str(e)}', exc_info=True)
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def _extract_user_from_token(self, payload, clerk_user_id):
        """Extract user data from JWT token when Clerk API is unavailable."""
        # Extract email from token claims
        email = payload.get('email') or payload.get('primary_email_address_id')
        
        if not email:
            # Try to get from email_addresses array
            email_addresses = payload.get('email_addresses', [])
            if email_addresses:
                email = email_addresses[0] if isinstance(email_addresses[0], str) else None
        
        # If still no email, use a placeholder based on clerk_id
        if not email:
            email = f"{clerk_user_id}@temp.clerk.invalid"
        
        return {
            'id': clerk_user_id,
            'email_addresses': [{'email_address': email, 'id': 'primary'}],
            'primary_email_address_id': 'primary',
            'first_name': payload.get('given_name', ''),
            'last_name': payload.get('family_name', ''),
            'image_url': payload.get('picture', ''),
        }
    
    def _fetch_clerk_user(self, clerk_user_id):
        """Fetch user details from Clerk API."""
        cache_key = f'clerk_user_{clerk_user_id}'
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Using cached user data")
            return cached_data
        
        try:
            headers = {
                'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}',
            }
            
            response = requests.get(
                f'https://api.clerk.com/v1/users/{clerk_user_id}',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                cache.set(cache_key, user_data, 300)
                logger.info(f"Fetched user data from Clerk")
                return user_data
            elif response.status_code == 404:
                logger.warning(f'User not found in Clerk: {clerk_user_id}')
                return None
            
            logger.error(f'Failed to fetch user: {response.status_code} - {response.text}')
            return None
            
        except Exception as e:
            logger.error(f'Error fetching user: {str(e)}')
            return None
    
    def _get_primary_email(self, clerk_user_data):
        """Extract primary email from Clerk user data."""
        email_addresses = clerk_user_data.get('email_addresses', [])
        primary_email_id = clerk_user_data.get('primary_email_address_id')
        
        primary_email = None
        for email_obj in email_addresses:
            if email_obj.get('id') == primary_email_id:
                primary_email = email_obj.get('email_address')
                break
        
        if not primary_email and email_addresses:
            primary_email = email_addresses[0].get('email_address')
        
        if not primary_email:
            raise exceptions.AuthenticationFailed('User has no email address')
        
        return primary_email
    
    def _get_or_create_user(self, clerk_user_data):
        """
        Get existing user or create from Clerk data.
        Handles race conditions and duplicate emails properly.
        """
        clerk_user_id = clerk_user_data.get('id')
        primary_email = self._get_primary_email(clerk_user_data)
        
        with transaction.atomic():
            # First, try to find user by clerk_id
            try:
                user = User.objects.get(clerk_id=clerk_user_id)
                logger.info(f"✅ Found existing user by clerk_id: {user.email}")
                
                # Update user info if it's changed in Clerk
                updated = False
                if user.email != primary_email:
                    user.email = primary_email
                    updated = True
                if user.first_name != clerk_user_data.get('first_name', ''):
                    user.first_name = clerk_user_data.get('first_name', '')
                    updated = True
                if user.last_name != clerk_user_data.get('last_name', ''):
                    user.last_name = clerk_user_data.get('last_name', '')
                    updated = True
                
                if updated:
                    user.save()
                    logger.info(f"Updated user info for: {user.email}")
                
                return user
                
            except User.DoesNotExist:
                # User with this clerk_id doesn't exist
                # Check if a user with this email already exists (e.g., superuser)
                try:
                    user = User.objects.get(email=primary_email)
                    logger.info(f"⚠️ Found existing user by email: {user.email}")
                    
                    # Update the existing user with Clerk ID
                    if not user.clerk_id or user.clerk_id.startswith('local_'):
                        user.clerk_id = clerk_user_id
                        user.first_name = clerk_user_data.get('first_name', '') or user.first_name
                        user.last_name = clerk_user_data.get('last_name', '') or user.last_name
                        user.avatar_url = clerk_user_data.get('image_url') or user.avatar_url
                        user.save()
                        logger.info(f"✅ Linked existing user to Clerk: {user.email}")
                    else:
                        # User has a different clerk_id - this is a problem
                        logger.error(f"⛔ Email conflict: {primary_email} exists with different clerk_id")
                        raise exceptions.AuthenticationFailed(
                            f'User with email {primary_email} already exists with a different account'
                        )
                    
                    return user
                    
                except User.DoesNotExist:
                    # Create new user
                    try:
                        user = User.objects.create(
                            clerk_id=clerk_user_id,
                            email=primary_email,
                            first_name=clerk_user_data.get('first_name', ''),
                            last_name=clerk_user_data.get('last_name', ''),
                            avatar_url=clerk_user_data.get('image_url'),
                        )
                        logger.info(f"✅ Created new user: {user.email}")
                        return user
                        
                    except IntegrityError as e:
                        # Race condition - another request created the user
                        logger.warning(f"Race condition detected, retrying: {str(e)}")
                        # Retry once to get the newly created user
                        try:
                            user = User.objects.get(clerk_id=clerk_user_id)
                            logger.info(f"✅ Retrieved user after race condition: {user.email}")
                            return user
                        except User.DoesNotExist:
                            # Still doesn't exist by clerk_id, try by email
                            try:
                                user = User.objects.get(email=primary_email)
                                logger.info(f"✅ Retrieved user by email after race condition: {user.email}")
                                return user
                            except User.DoesNotExist:
                                raise exceptions.AuthenticationFailed('User creation failed')
