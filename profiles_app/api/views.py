from rest_framework import generics

from profiles_app.models import UserProfile
from .serializers import ProfileDetailSerializer


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Shows and updates a profile. The pk in the URL is the user id."""

    queryset = UserProfile.objects.select_related('user')
    serializer_class = ProfileDetailSerializer
    lookup_field = 'user'
    lookup_url_kwarg = 'pk'
    http_method_names = ['get', 'patch', 'options']
