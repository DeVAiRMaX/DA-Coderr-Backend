from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from profiles_app.models import UserProfile
from .permissions import IsProfileOwnerOrReadOnly
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileDetailSerializer,
)


class ProfileViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """Shows and updates a profile. The pk in the URL is the user id."""

    queryset = UserProfile.objects.select_related('user')
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated & IsProfileOwnerOrReadOnly]
    lookup_field = 'user'
    lookup_url_kwarg = 'pk'
    lookup_value_regex = r'\d+'
    http_method_names = ['get', 'patch', 'options']


class BusinessProfileListView(generics.ListAPIView):
    """Lists the profiles of all business users."""

    queryset = UserProfile.objects.filter(
        type=UserProfile.BUSINESS
    ).select_related('user')
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(generics.ListAPIView):
    """Lists the profiles of all customers."""

    queryset = UserProfile.objects.filter(
        type=UserProfile.CUSTOMER
    ).select_related('user')
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
