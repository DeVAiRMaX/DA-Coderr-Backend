from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    BusinessProfileListView,
    CustomerProfileListView,
    ProfileViewSet,
)

router = SimpleRouter()
router.register('profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('profiles/business/', BusinessProfileListView.as_view(),
         name='business-profile-list'),
    path('profiles/customer/', CustomerProfileListView.as_view(),
         name='customer-profile-list'),
]
