from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Profiles in the admin, filterable by customer and business."""

    list_display = ['user', 'type', 'location', 'created_at']
    list_filter = ['type']
    search_fields = ['user__username', 'user__email', 'location']
