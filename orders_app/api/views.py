from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from orders_app.models import Order
from profiles_app.models import UserProfile
from .permissions import IsCustomerUser, IsOrderBusinessUser
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


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


class OrderUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """The business user of an order can change its status,
    only admins (staff) can delete orders."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    http_method_names = ['patch', 'delete', 'options']

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsOrderBusinessUser()]


def count_orders_of_business_user(business_user_id, order_status):
    """Counts the orders of a business user with the given status.
    Raises 404 if there is no business user with this id."""
    business_user = get_object_or_404(
        User, pk=business_user_id, profile__type=UserProfile.BUSINESS
    )
    return Order.objects.filter(
        business_user=business_user, status=order_status
    ).count()


class OrderCountView(APIView):
    """Number of orders in progress of a business user."""

    def get(self, request, business_user_id):
        count = count_orders_of_business_user(
            business_user_id, Order.IN_PROGRESS
        )
        return Response({'order_count': count})


class CompletedOrderCountView(APIView):
    """Number of completed orders of a business user."""

    def get(self, request, business_user_id):
        count = count_orders_of_business_user(
            business_user_id, Order.COMPLETED
        )
        return Response({'completed_order_count': count})
