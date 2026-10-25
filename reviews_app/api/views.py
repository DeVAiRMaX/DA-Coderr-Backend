from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from reviews_app.models import Review
from .filters import ReviewFilter
from .permissions import IsCustomerUser
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """Lists all reviews, filterable by business user and reviewer.
    Customers can review every business user once."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['updated_at', 'rating']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        business_user = serializer.validated_data['business_user']
        already_reviewed = Review.objects.filter(
            business_user=business_user, reviewer=self.request.user
        ).exists()
        if already_reviewed:
            raise PermissionDenied(
                'You have already reviewed this business user.'
            )
        serializer.save(reviewer=self.request.user)
