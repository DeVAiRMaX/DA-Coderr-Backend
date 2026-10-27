from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from reviews_app.models import Review
from .filters import ReviewFilter
from .permissions import IsCustomerUserToCreate, IsReviewer
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """Reviews, filterable by business user and reviewer. Customers can
    review every business user once, only the author may change or
    delete a review."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthenticated & IsCustomerUserToCreate & IsReviewer
    ]
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['updated_at', 'rating']

    def get_serializer_class(self):
        """On PATCH only rating and description can be changed."""
        if self.action == 'partial_update':
            return ReviewUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """A second review for the same business user is answered with 403."""
        business_user = serializer.validated_data['business_user']
        already_reviewed = Review.objects.filter(
            business_user=business_user, reviewer=self.request.user
        ).exists()
        if already_reviewed:
            raise PermissionDenied(
                'You have already reviewed this business user.'
            )
        serializer.save(reviewer=self.request.user)
