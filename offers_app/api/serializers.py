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
