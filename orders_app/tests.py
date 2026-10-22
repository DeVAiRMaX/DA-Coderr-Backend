from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from profiles_app.models import UserProfile
from .models import Order


def create_user_with_profile(username, profile_type):
    user = User.objects.create_user(username, f'{username}@mail.de', 'pw')
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def create_offer_detail(business_user):
    offer = Offer.objects.create(user=business_user, title='Logo Paket')
    return OfferDetail.objects.create(
        offer=offer, title='Basic Logo', revisions=3,
        delivery_time_in_days=5, price=150, features=['Logo', 'Favicon'],
        offer_type='basic',
    )


def create_order(customer, business, order_status=Order.IN_PROGRESS):
    return Order.objects.create(
        customer_user=customer, business_user=business, title='Logo',
        revisions=1, delivery_time_in_days=5, price=100,
        features=['Logo'], offer_type='basic', status=order_status,
    )


class OrderTestCase(APITestCase):
    """Creates the users that every order test needs."""

    def setUp(self):
        self.customer = create_user_with_profile('cus', UserProfile.CUSTOMER)
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.other = create_user_with_profile('other', UserProfile.BUSINESS)


class OrderModelTests(OrderTestCase):

    def test_str_shows_title_and_users(self):
        order = create_order(self.customer, self.business)
        self.assertEqual(str(order), 'Logo (cus -> biz)')


class OrderListTests(OrderTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('order-list')
        create_order(self.customer, self.business)
        create_order(self.customer, self.other)

    def test_customer_sees_own_orders(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_business_user_sees_only_own_orders(self):
        self.client.force_authenticate(self.business)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['business_user'], self.business.id)

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderCreateTests(OrderTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('order-list')
        self.offer_detail = create_offer_detail(self.business)
        self.data = {'offer_detail_id': self.offer_detail.id}

    def test_customer_can_create_order_from_offer_detail(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_user'], self.customer.id)
        self.assertEqual(response.data['business_user'], self.business.id)
        self.assertEqual(response.data['title'], 'Basic Logo')
        self.assertEqual(response.data['features'], ['Logo', 'Favicon'])
        self.assertEqual(response.data['status'], 'in_progress')

    def test_order_keeps_data_when_offer_changes(self):
        self.client.force_authenticate(self.customer)
        self.client.post(self.url, self.data, format='json')
        self.offer_detail.price = 999
        self.offer_detail.save()
        self.assertEqual(Order.objects.get().price, 150)

    def test_business_user_cannot_create_order(self):
        self.client.force_authenticate(self.business)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_requires_authentication(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_offer_detail_id_returns_400(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_offer_detail_id_returns_400(self):
        self.client.force_authenticate(self.customer)
        data = {'offer_detail_id': 'abc'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_offer_detail_returns_404(self):
        self.client.force_authenticate(self.customer)
        data = {'offer_detail_id': 9999}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderUpdateTests(OrderTestCase):

    def setUp(self):
        super().setUp()
        self.order = create_order(self.customer, self.business)
        self.url = reverse('order-detail', kwargs={'pk': self.order.id})
        self.client.force_authenticate(self.business)

    def test_business_user_can_change_status(self):
        data = {'status': 'completed'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.COMPLETED)

    def test_invalid_status_returns_400(self):
        response = self.client.patch(
            self.url, {'status': 'done'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_fields_return_400(self):
        data = {'status': 'completed', 'price': 1}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.price, 100)

    def test_missing_status_returns_400(self):
        response = self.client.patch(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_change_status(self):
        self.client.force_authenticate(self.customer)
        data = {'status': 'completed'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_business_user_cannot_change_status(self):
        self.client.force_authenticate(self.other)
        data = {'status': 'completed'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_authentication(self):
        self.client.force_authenticate(None)
        data = {'status': 'completed'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_unknown_order_returns_404(self):
        url = reverse('order-detail', kwargs={'pk': 9999})
        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderDeleteTests(OrderTestCase):

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user('admin', is_staff=True)
        self.order = create_order(self.customer, self.business)
        self.url = reverse('order-detail', kwargs={'pk': self.order.id})

    def test_admin_can_delete_order(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.exists())

    def test_business_user_cannot_delete_order(self):
        self.client.force_authenticate(self.business)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.exists())

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unknown_order_returns_404(self):
        self.client.force_authenticate(self.admin)
        url = reverse('order-detail', kwargs={'pk': 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderCountTests(OrderTestCase):

    def setUp(self):
        super().setUp()
        create_order(self.customer, self.business)
        create_order(self.customer, self.business)
        create_order(self.customer, self.business, Order.COMPLETED)
        create_order(self.customer, self.business, Order.CANCELLED)
        create_order(self.customer, self.other)
        self.client.force_authenticate(self.customer)

    def get_count(self, url_name, user_id):
        url = reverse(url_name, kwargs={'business_user_id': user_id})
        return self.client.get(url)

    def test_order_count_counts_orders_in_progress(self):
        response = self.get_count('order-count', self.business.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'order_count': 2})

    def test_completed_order_count_counts_completed_orders(self):
        response = self.get_count('completed-order-count', self.business.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'completed_order_count': 1})

    def test_unknown_business_user_returns_404(self):
        for url_name in ['order-count', 'completed-order-count']:
            response = self.get_count(url_name, 9999)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_id_returns_404(self):
        response = self.get_count('order-count', self.customer.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_counts_require_authentication(self):
        self.client.force_authenticate(None)
        response = self.get_count('order-count', self.business.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
