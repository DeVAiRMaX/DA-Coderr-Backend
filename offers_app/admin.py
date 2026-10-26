from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Shows the three packages directly below the offer."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Offers in the admin, including their packages."""

    list_display = ['title', 'user', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__username']
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """All offer packages, filterable by offer type."""

    list_display = ['offer', 'offer_type', 'price', 'delivery_time_in_days']
    list_filter = ['offer_type']
