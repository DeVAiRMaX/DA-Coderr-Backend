from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from reviews_app.models import Review
from .filters import ReviewFilter
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListAPIView):
    """Lists all reviews, filterable by business user and reviewer."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['updated_at', 'rating']
