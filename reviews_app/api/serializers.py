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
        """Only business users can be reviewed."""
        profile = getattr(value, 'profile', None)
        if profile is None or profile.type != UserProfile.BUSINESS:
            raise serializers.ValidationError(
                'Reviews can only be given to business users.'
            )
        return value


class ReviewUpdateSerializer(ReviewSerializer):
    """Only rating and description of a review can be changed."""

    EDITABLE_FIELDS = {'rating', 'description'}

    class Meta(ReviewSerializer.Meta):
        read_only_fields = ['business_user', 'reviewer']

    def validate(self, attrs):
        """Rejects every field except rating and description with a 400."""
        other_fields = set(self.initial_data) - self.EDITABLE_FIELDS
        if other_fields:
            raise serializers.ValidationError(
                f'Only rating and description can be changed, not: '
                f'{", ".join(sorted(other_fields))}.'
            )
        return attrs
