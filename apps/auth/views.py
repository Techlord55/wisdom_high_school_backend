# apps/auth/views.py
"""
Authentication views.

All authentication is now handled by Clerk.
This file is kept for potential future custom auth needs.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


# All login functionality is now handled by Clerk
# Teachers, admins, and students all use Clerk authentication
