from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import OfferDetailViewSet, OfferViewSet

router = SimpleRouter()
router.register('offers', OfferViewSet, basename='offer')
router.register('offerdetails', OfferDetailViewSet, basename='offerdetail')

urlpatterns = [
    path('', include(router.urls)),
]
