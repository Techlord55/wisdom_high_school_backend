"""
Management command to fix duplicate email issues and inspect user data.
"""
from django.core.management.base import BaseCommand
from apps.users.models import User
from django.db.models import Count


class Command(BaseCommand):
    help = 'Inspect and fix user database issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix duplicate email issues by merging users',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Specific email to inspect',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== User Database Inspection ===\n'))
        
        # Check for duplicate emails
        duplicates = (
            User.objects.values('email')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        if duplicates:
            self.stdout.write(self.style.ERROR(f'Found {duplicates.count()} duplicate emails:'))
            for dup in duplicates:
                email = dup['email']
                users = User.objects.filter(email=email).order_by('created_at')
                
                self.stdout.write(self.style.WARNING(f'\n📧 Email: {email} ({dup["count"]} users)'))
                for i, user in enumerate(users, 1):
                    self.stdout.write(
                        f'  {i}. ID: {user.id} | '
                        f'Clerk ID: {user.clerk_id or "NONE"} | '
                        f'Role: {user.role} | '
                        f'Staff: {user.is_staff} | '
                        f'Created: {user.created_at}'
                    )
                
                if options['fix']:
                    self._fix_duplicate(users)
        else:
            self.stdout.write(self.style.SUCCESS('✅ No duplicate emails found'))
        
        # If specific email requested
        if options['email']:
            self._inspect_email(options['email'])
        
        # Show summary
        self._show_summary()
    
    def _fix_duplicate(self, users):
        """Fix duplicate users by keeping the oldest one and updating it."""
        if len(users) < 2:
            return
        
        # Keep the first user (oldest)
        primary_user = users[0]
        duplicates = users[1:]
        
        self.stdout.write(self.style.WARNING(f'\n🔧 Fixing duplicates for {primary_user.email}...'))
        
        # If primary user has no clerk_id but duplicate does, use the duplicate's clerk_id
        for dup in duplicates:
            if dup.clerk_id and not primary_user.clerk_id.startswith('user_'):
                self.stdout.write(f'  → Updating clerk_id: {dup.clerk_id}')
                primary_user.clerk_id = dup.clerk_id
            
            if dup.avatar_url and not primary_user.avatar_url:
                self.stdout.write(f'  → Updating avatar_url')
                primary_user.avatar_url = dup.avatar_url
            
            # Delete the duplicate
            self.stdout.write(self.style.ERROR(f'  → Deleting duplicate user ID: {dup.id}'))
            dup.delete()
        
        primary_user.save()
        self.stdout.write(self.style.SUCCESS(f'✅ Fixed duplicates, kept user ID: {primary_user.id}'))
    
    def _inspect_email(self, email):
        """Inspect a specific email."""
        self.stdout.write(self.style.WARNING(f'\n🔍 Inspecting email: {email}'))
        
        users = User.objects.filter(email=email)
        if not users.exists():
            self.stdout.write(self.style.ERROR(f'❌ No users found with email: {email}'))
            return
        
        for user in users:
            self.stdout.write(f'\n📋 User Details:')
            self.stdout.write(f'  ID: {user.id}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Clerk ID: {user.clerk_id or "NONE"}')
            self.stdout.write(f'  Name: {user.first_name} {user.last_name}')
            self.stdout.write(f'  Role: {user.role}')
            self.stdout.write(f'  Staff: {user.is_staff}')
            self.stdout.write(f'  Superuser: {user.is_superuser}')
            self.stdout.write(f'  Active: {user.is_active}')
            self.stdout.write(f'  Created: {user.created_at}')
    
    def _show_summary(self):
        """Show database summary."""
        total_users = User.objects.count()
        with_clerk = User.objects.exclude(clerk_id__isnull=True).exclude(clerk_id='').count()
        local_users = User.objects.filter(clerk_id__startswith='local_').count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        self.stdout.write(self.style.WARNING('\n📊 Database Summary:'))
        self.stdout.write(f'  Total Users: {total_users}')
        self.stdout.write(f'  With Clerk ID: {with_clerk}')
        self.stdout.write(f'  Local Users: {local_users}')
        self.stdout.write(f'  Staff Users: {staff_users}')
