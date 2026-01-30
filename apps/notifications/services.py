# Location: .\apps\notifications\services.py
# ==================== apps/notifications/services.py ====================
from apps.payments.models import Notification
from apps.users.models import User


def create_notification(user: User, title: str, message: str) -> Notification:
    """Create a notification for a user."""
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message
    )
    
    # TODO: Send real-time notification via WebSocket/Pusher
    # TODO: Send email notification if configured
    
    return notification


def mark_notification_as_read(notification_id: str):
    """Mark notification as read."""
    
    notification = Notification.objects.get(id=notification_id)
    notification.is_read = True
    notification.save()
    
    return notification


def get_user_notifications(user: User, unread_only=False):
    """Get user notifications."""
    
    queryset = Notification.objects.filter(user=user)
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    return queryset.order_by('-created_at')

