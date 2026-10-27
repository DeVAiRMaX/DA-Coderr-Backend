from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from orders_app.models import Order
from profiles_app.models import UserProfile
from .permissions import (
    IsCustomerUserToCreate,
    IsOrderBusinessUserToUpdate,
    IsStaffToDelete,
)
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


class OrderViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    """Customers create orders, the business user of an order changes
    its status and only admins (staff) can delete orders."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [
        IsAuthenticated
        & IsCustomerUserToCreate
        & IsStaffToDelete
        & IsOrderBusinessUserToUpdate
    ]
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_queryset(self):
        """The list only shows orders the user is customer or business of."""
        if self.action == 'list':
            user = self.request.user
            return Order.objects.filter(
                Q(customer_user=user) | Q(business_user=user)
            )
        return super().get_queryset()

    def get_serializer_class(self):
        """On PATCH only the status can be changed."""
        if self.action == 'partial_update':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """Takes an offer_detail_id and answers with the full order."""
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

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        count = count_orders_of_business_user(
            business_user_id, Order.IN_PROGRESS
        )
        return Response({'order_count': count})


class CompletedOrderCountView(APIView):
    """Number of completed orders of a business user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        count = count_orders_of_business_user(
            business_user_id, Order.COMPLETED
        )
        return Response({'completed_order_count': count})
