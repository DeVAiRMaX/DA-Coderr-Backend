import django_filters

from offers_app.models import Offer


class OfferFilter(django_filters.FilterSet):
    """Query filters of the offer list. Empty values are ignored."""

    creator_id = django_filters.NumberFilter(field_name='user_id')
    # min_price and min_delivery_time come from annotate() in the view
    min_price = django_filters.NumberFilter(
        field_name='min_price', lookup_expr='gte'
    )
    max_delivery_time = django_filters.NumberFilter(
        field_name='min_delivery_time', lookup_expr='lte'
    )

    class Meta:
        model = Offer
        fields = ['creator_id', 'min_price', 'max_delivery_time']
