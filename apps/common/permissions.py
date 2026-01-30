# Location: .\apps\common\permissions.py
# ==================== apps/common/permissions.py ====================
from rest_framework import permissions


class IsStudent(permissions.BasePermission):
    """Permission class for students."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'student'


class IsTeacher(permissions.BasePermission):
    """Permission class for teachers."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'teacher'


class IsAdmin(permissions.BasePermission):
    """Permission class for admins."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsTeacherOrAdmin(permissions.BasePermission):
    """Permission class for teachers or admins."""
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['teacher', 'admin'])
