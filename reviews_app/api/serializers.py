from rest_framework import serializers

from profiles_app.models import UserProfile
from reviews_app.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """All data of a review as described in the API docs."""

    class Meta:
        model = Review
        fields = [
            'id', 'business_user', 'reviewer', 'rating', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['reviewer']

    def validate_business_user(self, value):
        profile = getattr(value, 'profile', None)
        if profile is None or profile.type != UserProfile.BUSINESS:
            raise serializers.ValidationError(
                'Reviews can only be given to business users.'
            )
        return value
