# Location: .\apps\users\services.py
# ==================== apps/users/services.py ====================
from apps.users.models import User


def create_user_from_clerk(clerk_data: dict) -> User:
    """Create user from Clerk webhook data."""
    email = clerk_data['email_addresses'][0]['email_address']
    
    user, created = User.objects.get_or_create(
        clerk_id=clerk_data['id'],
        defaults={
            'email': email,
            'first_name': clerk_data.get('first_name', ''),
            'last_name': clerk_data.get('last_name', ''),
            'avatar_url': clerk_data.get('image_url'),
        }
    )
    
    return user


def update_user_from_clerk(clerk_data: dict) -> User:
    """Update user from Clerk webhook data."""
    user = User.objects.get(clerk_id=clerk_data['id'])
    
    email = clerk_data['email_addresses'][0]['email_address']
    user.email = email
    user.first_name = clerk_data.get('first_name', user.first_name)
    user.last_name = clerk_data.get('last_name', user.last_name)
    user.avatar_url = clerk_data.get('image_url', user.avatar_url)
    user.save()
    
    return user


def delete_user_by_clerk_id(clerk_id: str):
    """Delete user by Clerk ID."""
    User.objects.filter(clerk_id=clerk_id).delete()

