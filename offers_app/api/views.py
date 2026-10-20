from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from offers_app.models import Offer
from .permissions import IsBusinessUser
from .serializers import OfferWriteSerializer


class OfferListCreateView(generics.ListCreateAPIView):
    """Lists all offers (public) and lets business users create new ones."""

    queryset = Offer.objects.prefetch_related('details')
    serializer_class = OfferWriteSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsBusinessUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
