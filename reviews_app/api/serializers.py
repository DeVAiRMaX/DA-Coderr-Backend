from rest_framework import serializers

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
