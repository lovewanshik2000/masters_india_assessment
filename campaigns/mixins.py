"""
Custom permission mixins for view-based access control.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


class ViewPermissionMixin(LoginRequiredMixin):
    """
    Mixin that allows any authenticated user to view (read-only access).
    Use this for list views and detail views that should be accessible to all logged-in users.
    """
    pass


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires staff status for create/update/delete operations.
    Use this for views that modify data.
    """
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to perform this action. Staff access required.")
        return redirect('dashboard')
