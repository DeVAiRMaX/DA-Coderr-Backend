from django.urls import path

from .views import (
    OfferDetailRetrieveView,
    OfferListCreateView,
    OfferRetrieveUpdateDestroyView,
)

urlpatterns = [
    path('offers/', OfferListCreateView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', OfferRetrieveUpdateDestroyView.as_view(),
         name='offer-detail'),
    path('offerdetails/<int:pk>/', OfferDetailRetrieveView.as_view(),
         name='offerdetail-detail'),
]
