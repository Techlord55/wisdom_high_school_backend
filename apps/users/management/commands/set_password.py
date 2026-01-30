"""
Management command to set password for a user.

Usage:
    python manage.py set_password <email> <password>

Example:
    python manage.py set_password teacher@example.com TempPassword123!
"""
from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User


class Command(BaseCommand):
    help = 'Set password for a user by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('password', type=str, help='New password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist')
        
        # Set the password
        user.set_password(password)
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Password successfully set for {user.full_name} ({email})'
            )
        )
        self.stdout.write(f'   Role: {user.role}')
        self.stdout.write(f'   Active: {user.is_active}')
        
        if user.role == 'teacher':
            if hasattr(user, 'teacher_profile'):
                self.stdout.write(f'   Teacher ID: {user.teacher_profile.teacher_id}')
