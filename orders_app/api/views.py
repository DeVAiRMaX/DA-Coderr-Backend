from django.db.models import Q
from rest_framework import generics

from orders_app.models import Order
from .serializers import OrderSerializer


class OrderListCreateView(generics.ListAPIView):
    """Lists the orders the user is part of, as customer or as business."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )
