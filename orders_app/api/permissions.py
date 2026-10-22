from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUser(BasePermission):
    """Only users with a customer profile get access."""

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == UserProfile.CUSTOMER


class IsOrderBusinessUser(BasePermission):
    """Only the business user of this order may change it."""

    def has_object_permission(self, request, view, obj):
        return obj.business_user == request.user
