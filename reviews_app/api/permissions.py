from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUserToCreate(BasePermission):
    """Only users with a customer profile may create reviews."""

    def has_permission(self, request, view):
        if view.action != 'create':
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.CUSTOMER


class IsReviewer(BasePermission):
    """Only the user who wrote the review may change or delete it."""

    def has_object_permission(self, request, view, obj):
        return obj.reviewer == request.user
