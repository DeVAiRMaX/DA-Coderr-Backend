from django.contrib.auth.models import User
from django.db import models

from offers_app.models import OfferDetail


class Order(models.Model):
    """An order of an offer package. The package data is copied on purpose,
    so later changes to the offer don't change existing orders."""

    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (IN_PROGRESS, 'In progress'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    customer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='customer_orders'
    )
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='business_orders'
    )
    offer_detail = models.ForeignKey(
        OfferDetail, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders',
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(
        max_length=10, choices=OfferDetail.OFFER_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=IN_PROGRESS
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.customer_user} -> {self.business_user})'
