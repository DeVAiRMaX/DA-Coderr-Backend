from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from offers_app.models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import IsBusinessUser
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


def get_offer_queryset():
    """All offers with their cheapest price and fastest delivery time."""
    # order_by is needed here: Django ignores Meta.ordering after annotate()
    return Offer.objects.select_related('user').prefetch_related(
        'details'
    ).annotate(
        min_price=Min('details__price'),
        min_delivery_time=Min('details__delivery_time_in_days'),
    ).order_by('-updated_at')


class OfferListCreateView(generics.ListCreateAPIView):
    """Lists all offers (public) and lets business users create new ones."""

    pagination_class = OfferPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']

    def get_queryset(self):
        return get_offer_queryset()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsBusinessUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferRetrieveUpdateDestroyView(generics.RetrieveUpdateAPIView):
    """Shows and updates a single offer."""

    http_method_names = ['get', 'patch', 'options']

    def get_queryset(self):
        return get_offer_queryset()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return OfferWriteSerializer
        return OfferRetrieveSerializer


class OfferDetailRetrieveView(generics.RetrieveAPIView):
    """Shows a single offer package."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
