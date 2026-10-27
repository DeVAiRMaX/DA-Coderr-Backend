from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUserToCreate(BasePermission):
    """Only users with a customer profile may create orders."""

    def has_permission(self, request, view):
        if view.action != 'create':
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.CUSTOMER


class IsStaffToDelete(BasePermission):
    """Only admins (staff) may delete orders."""

    def has_permission(self, request, view):
        if view.action != 'destroy':
            return True
        return request.user.is_staff


class IsOrderBusinessUserToUpdate(BasePermission):
    """Only the business user of this order may change its status."""

    def has_object_permission(self, request, view, obj):
        if view.action != 'partial_update':
            return True
        return obj.business_user == request.user
