from django.urls import path

from .views import OrderListCreateView, OrderUpdateDestroyView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderUpdateDestroyView.as_view(),
         name='order-detail'),
]
