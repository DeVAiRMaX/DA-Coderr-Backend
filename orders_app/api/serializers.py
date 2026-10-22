from rest_framework import serializers

from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """All data of an order as described in the API docs."""

    class Meta:
        model = Order
        fields = [
            'id', 'customer_user', 'business_user', 'title', 'revisions',
            'delivery_time_in_days', 'price', 'features', 'offer_type',
            'status', 'created_at', 'updated_at',
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Creates an order from an offer package (OfferDetail)."""

    offer_detail_id = serializers.IntegerField()

    def create(self, validated_data):
        """Copies the package data, so the order keeps its original terms."""
        offer_detail = validated_data['offer_detail']
        return Order.objects.create(
            customer_user=validated_data['customer_user'],
            business_user=offer_detail.offer.user,
            offer_detail=offer_detail,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
        )
