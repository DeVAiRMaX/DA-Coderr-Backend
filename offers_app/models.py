from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Offer(models.Model):
    """A service offered by a business user, sold in three packages."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='offers'
    )
    title = models.CharField(max_length=255)
    image = models.FileField(upload_to='offer_images/', blank=True, null=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """One package (basic, standard or premium) of an offer."""

    BASIC = 'basic'
    STANDARD = 'standard'
    PREMIUM = 'premium'
    OFFER_TYPE_CHOICES = [
        (BASIC, 'Basic'),
        (STANDARD, 'Standard'),
        (PREMIUM, 'Premium'),
    ]

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name='details'
    )
    title = models.CharField(max_length=255)
    # -1 means unlimited revisions (that's how the frontend sends it)
    revisions = models.IntegerField(validators=[MinValueValidator(-1)])
    delivery_time_in_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)

    class Meta:
        verbose_name = 'Offer detail'
        verbose_name_plural = 'Offer details'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['offer', 'offer_type'], name='unique_offer_type'
            ),
        ]

    def __str__(self):
        return f'{self.offer.title} ({self.offer_type})'
