# Location: .\apps\users\selectors.py
# ==================== apps/users/selectors.py ====================
from apps.users.models import User


def get_user_by_clerk_id(clerk_id: str) -> User:
    """Get user by Clerk ID."""
    return User.objects.get(clerk_id=clerk_id)


def get_all_users(role=None, is_active=True):
    """Get all users with optional filtering."""
    queryset = User.objects.filter(is_active=is_active)
    
    if role:
        queryset = queryset.filter(role=role)
    
    return queryset
