from django.contrib.auth.models import User
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

REQUIRED_OFFER_TYPES = {
    OfferDetail.BASIC, OfferDetail.STANDARD, OfferDetail.PREMIUM
}


class OfferDetailSerializer(serializers.ModelSerializer):
    """All data of a single offer package."""

    features = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type',
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Short version of a package: only its id and the link to it."""

    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail')

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class UserDetailsSerializer(serializers.ModelSerializer):
    """Name of the business user who created the offer."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']


class OfferListSerializer(serializers.ModelSerializer):
    """Offer as shown in the offer list, including the cheapest price."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    # Both values are calculated in the view with annotate()
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = UserDetailsSerializer(source='user', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
            'user_details',
        ]


class OfferRetrieveSerializer(OfferListSerializer):
    """Single offer. Same as in the list, but without user_details."""

    class Meta(OfferListSerializer.Meta):
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
        ]


class OfferWriteSerializer(serializers.ModelSerializer):
    """Creates or updates an offer together with its packages."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        """On POST exactly one basic, standard and premium detail is needed."""
        if self.partial:
            return self.validate_partial_details(value)
        offer_types = [detail['offer_type'] for detail in value]
        if len(value) != 3 or set(offer_types) != REQUIRED_OFFER_TYPES:
            raise serializers.ValidationError(
                'An offer needs exactly three details: '
                'basic, standard and premium.'
            )
        return value

    def validate_partial_details(self, value):
        """On PATCH every detail is identified by its offer_type."""
        offer_types = [detail.get('offer_type') for detail in value]
        if None in offer_types:
            raise serializers.ValidationError(
                'Every detail needs its offer_type.'
            )
        existing_types = self.instance.details.values_list(
            'offer_type', flat=True
        )
        if not set(offer_types) <= set(existing_types):
            raise serializers.ValidationError(
                'This offer has no detail with this offer_type.'
            )
        return value

    def create(self, validated_data):
        """Creates the offer first, then its three details."""
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        """Updates the offer fields and every sent detail."""
        details_data = validated_data.pop('details', [])
        instance = super().update(instance, validated_data)
        for detail_data in details_data:
            self.update_detail(instance, detail_data)
        return instance

    def update_detail(self, offer, detail_data):
        """Changes only the sent fields, so the detail keeps its id."""
        detail = offer.details.get(offer_type=detail_data['offer_type'])
        for field, value in detail_data.items():
            setattr(detail, field, value)
        detail.save()
