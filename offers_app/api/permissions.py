from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsBusinessUser(BasePermission):
    """Only users with a business profile get access."""

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.BUSINESS
