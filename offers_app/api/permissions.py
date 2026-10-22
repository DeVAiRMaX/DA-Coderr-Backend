from rest_framework.permissions import SAFE_METHODS, BasePermission

from profiles_app.models import UserProfile


class IsBusinessUser(BasePermission):
    """Only users with a business profile get access."""

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.BUSINESS


class IsOfferOwnerOrReadOnly(BasePermission):
    """Everyone may read an offer, only its creator may change or delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
