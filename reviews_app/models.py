from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A rating (1 to 5 stars) a customer gives a business user."""

    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_reviews'
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='written_reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-updated_at']
        # A customer may review every business user only once
        constraints = [
            models.UniqueConstraint(
                fields=['business_user', 'reviewer'],
                name='unique_review_per_business_user',
            ),
        ]

    def __str__(self):
        return f'{self.reviewer} -> {self.business_user}: {self.rating}'
