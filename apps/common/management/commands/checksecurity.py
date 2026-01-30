"""
Management command to check security configuration.

Usage:
    python manage.py checksecurity
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Check security configuration and best practices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Enable strict mode with all security checks',
        )

    def handle(self, *args, **options):
        strict = options['strict']
        issues = []
        warnings = []
        passed = []

        self.stdout.write(self.style.HTTP_INFO('\n🔒 Security Configuration Check\n'))
        self.stdout.write('=' * 70)

        # Check DEBUG
        if settings.DEBUG:
            issues.append('❌ DEBUG is True - MUST be False in production!')
        else:
            passed.append('✅ DEBUG is False')

        # Check SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-' or len(settings.SECRET_KEY) < 50:
            issues.append('❌ SECRET_KEY is weak or default - generate a strong one!')
        else:
            passed.append('✅ SECRET_KEY appears strong')

        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            issues.append('❌ ALLOWED_HOSTS not properly configured!')
        else:
            passed.append(f'✅ ALLOWED_HOSTS configured: {", ".join(settings.ALLOWED_HOSTS[:3])}')

        # Check HTTPS settings
        if not settings.DEBUG:
            if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
                issues.append('❌ SECURE_SSL_REDIRECT not enabled!')
            else:
                passed.append('✅ SECURE_SSL_REDIRECT enabled')

            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                issues.append('❌ SESSION_COOKIE_SECURE not enabled!')
            else:
                passed.append('✅ SESSION_COOKIE_SECURE enabled')

            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                issues.append('❌ CSRF_COOKIE_SECURE not enabled!')
            else:
                passed.append('✅ CSRF_COOKIE_SECURE enabled')

            hsts = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
            if hsts < 31536000:  # 1 year
                warnings.append(f'⚠️  SECURE_HSTS_SECONDS is {hsts}, should be 31536000 (1 year)')
            else:
                passed.append('✅ SECURE_HSTS_SECONDS properly configured')

        # Check CORS
        if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
            issues.append('❌ CORS_ALLOW_ALL_ORIGINS is True - security risk!')
        else:
            passed.append('✅ CORS_ALLOW_ALL_ORIGINS is False')

        # Check database SSL
        db_config = settings.DATABASES.get('default', {})
        if 'OPTIONS' in db_config and not settings.DEBUG:
            if 'sslmode' not in db_config.get('OPTIONS', {}):
                warnings.append('⚠️  Database SSL not configured')
            else:
                passed.append('✅ Database SSL configured')

        # Check .env file
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if not os.path.exists(env_path):
            warnings.append('⚠️  .env file not found - using defaults?')
        else:
            passed.append('✅ .env file found')

        # Check for example .env values
        if 'your-secret-key' in settings.SECRET_KEY.lower():
            issues.append('❌ Using example SECRET_KEY - REPLACE IMMEDIATELY!')

        # Print results
        self.stdout.write('\n' + self.style.SUCCESS('Passed Checks:'))
        for check in passed:
            self.stdout.write(f'  {check}')

        if warnings:
            self.stdout.write('\n' + self.style.WARNING('Warnings:'))
            for warning in warnings:
                self.stdout.write(f'  {warning}')

        if issues:
            self.stdout.write('\n' + self.style.ERROR('Critical Issues:'))
            for issue in issues:
                self.stdout.write(f'  {issue}')
            self.stdout.write('\n' + self.style.ERROR(f'\n⚠️  Found {len(issues)} critical security issues!'))
            self.stdout.write(self.style.ERROR('Please fix these before deploying to production.\n'))
            return
        else:
            self.stdout.write('\n' + self.style.SUCCESS('✅ All security checks passed!\n'))

        if strict and warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Strict mode: {len(warnings)} warnings found.\n'))
        
        self.stdout.write('=' * 70 + '\n')
