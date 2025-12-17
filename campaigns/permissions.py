"""
Custom permission classes for API views.
"""
from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Read-only access (GET, HEAD, OPTIONS) for any authenticated user
    - Write access (POST, PUT, PATCH, DELETE) only for staff users
    """
    
    def has_permission(self, request, view):
        # Allow authenticated users to read
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only staff can write
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsStaffUser(permissions.BasePermission):
    """
    Permission class that only allows staff users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
