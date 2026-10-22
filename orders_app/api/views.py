from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from offers_app.models import OfferDetail
from orders_app.models import Order
from .permissions import IsCustomerUser
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """Lists the orders the user is part of, as customer or as business.
    Customers can create new orders."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer_detail = get_object_or_404(
            OfferDetail, pk=serializer.validated_data['offer_detail_id']
        )
        order = serializer.save(
            customer_user=request.user, offer_detail=offer_detail
        )
        data = OrderSerializer(order).data
        return Response(data, status=status.HTTP_201_CREATED)
