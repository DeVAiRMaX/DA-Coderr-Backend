from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from profiles_app.models import UserProfile
from .permissions import IsProfileOwnerOrReadOnly
from .serializers import ProfileDetailSerializer


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Shows and updates a profile. The pk in the URL is the user id."""

    queryset = UserProfile.objects.select_related('user')
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated & IsProfileOwnerOrReadOnly]
    lookup_field = 'user'
    lookup_url_kwarg = 'pk'
    http_method_names = ['get', 'patch', 'options']
