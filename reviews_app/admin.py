from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Reviews in the admin, filterable by rating."""

    list_display = ['business_user', 'reviewer', 'rating', 'updated_at']
    list_filter = ['rating']
    search_fields = ['business_user__username', 'reviewer__username']
