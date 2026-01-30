# Location: .\apps\notifications\tasks.py
# ==================== apps/notifications/tasks.py ====================
from celery import shared_task
from apps.notifications.services import create_notification
from apps.users.models import User


@shared_task
def send_grade_notification(student_id: str, grade_data: dict):
    """Send notification when new grade is added."""
    
    try:
        user = User.objects.get(id=student_id)
        
        create_notification(
            user=user,
            title='New Grade Added',
            message=f"Your grade for {grade_data['subject']} - {grade_data['exam_name']} has been posted."
        )
    except User.DoesNotExist:
        pass


@shared_task
def send_payment_confirmation(student_id: str, amount: float):
    """Send notification when payment is confirmed."""
    
    try:
        user = User.objects.get(id=student_id)
        
        create_notification(
            user=user,
            title='Payment Confirmed',
            message=f"Your payment of {amount} FCFA has been successfully processed."
        )
    except User.DoesNotExist:
        pass


@shared_task
def send_assignment_notification(student_ids: list, assignment_title: str):
    """Send notification for new assignment."""
    
    for student_id in student_ids:
        try:
            user = User.objects.get(id=student_id)
            
            create_notification(
                user=user,
                title='New Assignment',
                message=f"A new assignment '{assignment_title}' has been posted."
            )
        except User.DoesNotExist:
            continue
