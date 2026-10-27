from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from offers_app.models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import (
    IsAuthenticatedOrListOnly,
    IsBusinessUserToCreate,
    IsOfferOwnerOrReadOnly,
)
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


class OfferViewSet(viewsets.ModelViewSet):
    """Offers with their cheapest price and fastest delivery time.
    The list is public, creating is only for business users and
    only the creator may change or delete an offer."""

    # order_by is needed here: Django ignores Meta.ordering after annotate()
    queryset = Offer.objects.select_related('user').prefetch_related(
        'details'
    ).annotate(
        min_price=Min('details__price'),
        min_delivery_time=Min('details__delivery_time_in_days'),
    ).order_by('-updated_at')
    serializer_class = OfferListSerializer
    permission_classes = [
        IsAuthenticatedOrListOnly
        & IsBusinessUserToCreate
        & IsOfferOwnerOrReadOnly
    ]
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']
    pagination_class = OfferPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']

    def get_serializer_class(self):
        """Each action shows the offer in the form the API docs describe."""
        if self.action in ['create', 'partial_update']:
            return OfferWriteSerializer
        if self.action == 'retrieve':
            return OfferRetrieveSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        """The logged in user always becomes the creator of the offer."""
        serializer.save(user=self.request.user)


class OfferDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Shows a single offer package."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
