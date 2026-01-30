# Location: .\apps\auth\permissions.py
# ==================== apps/auth/permissions.py ====================
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Permission to only allow admin users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to only allow owners or admins to edit."""
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.role == 'admin':
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user