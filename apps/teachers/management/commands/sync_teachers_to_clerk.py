# apps/teachers/management/commands/sync_teachers_to_clerk.py
"""
Management command to sync existing teachers to Clerk.
This is useful for migrating teachers who were created before Clerk integration.

Usage:
    python manage.py sync_teachers_to_clerk
    python manage.py sync_teachers_to_clerk --dry-run  # Test without making changes
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string
from apps.teachers.models import Teacher
from apps.teachers.clerk_sync import create_teacher_in_clerk
from apps.users.models import User


class Command(BaseCommand):
    help = 'Sync existing teachers to Clerk authentication system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making actual changes',
        )
        parser.add_argument(
            '--send-invitations',
            action='store_true',
            help='Send invitation emails to teachers',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_invitations = options['send_invitations']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find all teachers without clerk_id
        teachers_without_clerk = Teacher.objects.filter(
            user__clerk_id__isnull=True
        ).select_related('user')
        
        total_teachers = teachers_without_clerk.count()
        
        if total_teachers == 0:
            self.stdout.write(self.style.SUCCESS('✓ All teachers are already synced to Clerk'))
            return
        
        self.stdout.write(f'Found {total_teachers} teacher(s) to sync to Clerk')
        self.stdout.write('')
        
        synced_count = 0
        error_count = 0
        
        for teacher in teachers_without_clerk:
            user = teacher.user
            
            self.stdout.write(f'Processing: {user.full_name} ({user.email})')
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'  [DRY RUN] Would create Clerk user for {user.email}'))
                synced_count += 1
                continue
            
            try:
                # Generate a temporary password
                temp_password = get_random_string(16)
                
                # Create user in Clerk
                clerk_user = create_teacher_in_clerk(
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    password=temp_password,
                    send_invitation=send_invitations
                )
                
                # Update user with clerk_id
                user.clerk_id = clerk_user['id']
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created Clerk user: {clerk_user["id"]}'))
                
                if send_invitations:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Sent invitation email to {user.email}'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠ Temporary password: {temp_password} '
                        f'(teacher should reset password)'
                    ))
                
                synced_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                error_count += 1
            
            self.stdout.write('')
        
        # Summary
        self.stdout.write('─' * 50)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully synced: {synced_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {error_count}'))
        
        if not dry_run and synced_count > 0 and not send_invitations:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'IMPORTANT: Teachers have been assigned temporary passwords. '
                'They should use the "Forgot Password" feature at /sign-in to set their own passwords.'
            ))
