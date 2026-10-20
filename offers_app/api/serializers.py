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


class OfferWriteSerializer(serializers.ModelSerializer):
    """Creates an offer together with its three packages."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        offer_types = [detail['offer_type'] for detail in value]
        if len(value) != 3 or set(offer_types) != REQUIRED_OFFER_TYPES:
            raise serializers.ValidationError(
                'An offer needs exactly three details: '
                'basic, standard and premium.'
            )
        return value

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer
