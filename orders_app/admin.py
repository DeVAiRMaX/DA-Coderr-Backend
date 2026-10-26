from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Orders in the admin, filterable by status and offer type."""

    list_display = [
        'title', 'customer_user', 'business_user', 'status', 'created_at'
    ]
    list_filter = ['status', 'offer_type']
    search_fields = [
        'title', 'customer_user__username', 'business_user__username'
    ]
