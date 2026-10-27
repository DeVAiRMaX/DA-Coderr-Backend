from rest_framework.permissions import SAFE_METHODS, BasePermission

from profiles_app.models import UserProfile


class IsAuthenticatedOrListOnly(BasePermission):
    """The offer list is public, everything else needs a login."""

    def has_permission(self, request, view):
        if view.action == 'list':
            return True
        return request.user.is_authenticated


class IsBusinessUserToCreate(BasePermission):
    """Only users with a business profile may create offers."""

    def has_permission(self, request, view):
        if view.action != 'create':
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.BUSINESS


class IsOfferOwnerOrReadOnly(BasePermission):
    """Everyone may read an offer, only its creator may change or delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
