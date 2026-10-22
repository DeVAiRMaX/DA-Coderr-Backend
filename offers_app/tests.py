import copy
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profiles_app.models import UserProfile
from .models import Offer, OfferDetail

OFFER_DATA = {
    'title': 'Grafikdesign-Paket',
    'image': None,
    'description': 'Ein umfassendes Grafikdesign-Paket.',
    'details': [
        {'title': 'Basic', 'revisions': 2, 'delivery_time_in_days': 5,
         'price': 100, 'features': ['Logo'], 'offer_type': 'basic'},
        {'title': 'Standard', 'revisions': 5, 'delivery_time_in_days': 7,
         'price': 200, 'features': ['Logo', 'Flyer'],
         'offer_type': 'standard'},
        {'title': 'Premium', 'revisions': -1, 'delivery_time_in_days': 10,
         'price': 500, 'features': ['Logo', 'Flyer', 'Web'],
         'offer_type': 'premium'},
    ],
}

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def create_user_with_profile(username, profile_type):
    user = User.objects.create_user(username, f'{username}@mail.de', 'pw')
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def create_offer(user, title='Offer', price=100, days=5, description=''):
    """Creates an offer with one basic detail, enough for list tests."""
    offer = Offer.objects.create(
        user=user, title=title, description=description
    )
    OfferDetail.objects.create(
        offer=offer, title='Basic', revisions=1, delivery_time_in_days=days,
        price=price, features=['Logo'], offer_type='basic',
    )
    return offer


def create_full_offer(user):
    """Creates an offer with all three details from OFFER_DATA."""
    offer = Offer.objects.create(user=user, title=OFFER_DATA['title'])
    for detail_data in OFFER_DATA['details']:
        OfferDetail.objects.create(offer=offer, **detail_data)
    return offer


class OfferModelTests(APITestCase):

    def test_str_methods(self):
        user = create_user_with_profile('biz', UserProfile.BUSINESS)
        offer = create_offer(user, title='Logo Design')
        self.assertEqual(str(offer), 'Logo Design')
        self.assertEqual(str(offer.details.first()), 'Logo Design (basic)')


class OfferCreateTests(APITestCase):

    def setUp(self):
        self.url = reverse('offer-list')
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.customer = create_user_with_profile('cus', UserProfile.CUSTOMER)
        self.data = copy.deepcopy(OFFER_DATA)
        self.client.force_authenticate(self.business)

    def test_business_user_can_create_offer(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        offer = Offer.objects.get(id=response.data['id'])
        self.assertEqual(offer.user, self.business)
        self.assertEqual(offer.details.count(), 3)
        self.assertEqual(len(response.data['details']), 3)
        self.assertIn('id', response.data['details'][0])

    def test_unlimited_revisions_are_saved_as_minus_one(self):
        self.client.post(self.url, self.data, format='json')
        detail = OfferDetail.objects.get(offer_type='premium')
        self.assertEqual(detail.revisions, -1)

    def test_customer_cannot_create_offer(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_offer_needs_three_details(self):
        self.data['details'] = self.data['details'][:2]
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Offer.objects.exists())

    def test_offer_types_must_be_different(self):
        self.data['details'][2]['offer_type'] = 'basic'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revisions_below_minus_one_are_invalid(self):
        self.data['details'][0]['revisions'] = -2
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_title_is_required(self):
        del self.data['title']
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferListTests(APITestCase):

    def setUp(self):
        self.url = reverse('offer-list')
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.other = create_user_with_profile('other', UserProfile.BUSINESS)

    def get_titles(self, query=''):
        response = self.client.get(f'{self.url}?{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [offer['title'] for offer in response.data['results']]

    def test_list_is_public_and_paginated(self):
        for number in range(8):
            create_offer(self.business, title=f'Offer {number}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 6)
        self.assertIsNotNone(response.data['next'])

    def test_page_size_can_be_changed(self):
        for number in range(3):
            create_offer(self.business, title=f'Offer {number}')
        response = self.client.get(f'{self.url}?page_size=2')
        self.assertEqual(len(response.data['results']), 2)

    def test_list_contains_min_values_and_user_details(self):
        offer = create_offer(self.business, price=80, days=3)
        OfferDetail.objects.create(
            offer=offer, title='Standard', revisions=1,
            delivery_time_in_days=7, price=150, features=['x'],
            offer_type='standard',
        )
        result = self.client.get(self.url).data['results'][0]
        self.assertEqual(result['min_price'], 80)
        self.assertEqual(result['min_delivery_time'], 3)
        self.assertEqual(result['user_details']['username'], 'biz')
        self.assertIn('/api/offerdetails/', result['details'][0]['url'])

    def test_newest_offer_comes_first(self):
        create_offer(self.business, title='Old')
        create_offer(self.business, title='New')
        self.assertEqual(self.get_titles(), ['New', 'Old'])

    def test_filter_by_creator(self):
        create_offer(self.business, title='Mine')
        create_offer(self.other, title='Not mine')
        titles = self.get_titles(f'creator_id={self.business.id}')
        self.assertEqual(titles, ['Mine'])

    def test_filter_by_min_price(self):
        create_offer(self.business, title='Cheap', price=50)
        create_offer(self.business, title='Expensive', price=300)
        self.assertEqual(self.get_titles('min_price=100'), ['Expensive'])

    def test_filter_by_max_delivery_time(self):
        create_offer(self.business, title='Fast', days=2)
        create_offer(self.business, title='Slow', days=14)
        self.assertEqual(self.get_titles('max_delivery_time=7'), ['Fast'])

    def test_search_in_title_and_description(self):
        create_offer(self.business, title='Logo Design')
        create_offer(self.business, title='Website', description='design')
        create_offer(self.business, title='Texte')
        titles = self.get_titles('search=design')
        self.assertCountEqual(titles, ['Logo Design', 'Website'])

    def test_ordering_by_min_price(self):
        create_offer(self.business, title='B', price=200)
        create_offer(self.business, title='A', price=100)
        self.assertEqual(self.get_titles('ordering=min_price'), ['A', 'B'])
        self.assertEqual(self.get_titles('ordering=-min_price'), ['B', 'A'])

    def test_empty_query_params_are_ignored(self):
        create_offer(self.business, title='Offer')
        query = 'creator_id=&search=&ordering=&page=1&max_delivery_time='
        self.assertEqual(self.get_titles(query), ['Offer'])

    def test_invalid_query_param_returns_400(self):
        response = self.client.get(f'{self.url}?creator_id=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferDetailRetrieveTests(APITestCase):

    def setUp(self):
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.detail = create_offer(self.business).details.first()
        self.url = reverse('offerdetail-detail', kwargs={'pk': self.detail.id})

    def test_get_offer_detail(self):
        self.client.force_authenticate(self.business)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offer_type'], 'basic')
        self.assertEqual(response.data['features'], ['Logo'])

    def test_offer_detail_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_offer_detail_returns_404(self):
        self.client.force_authenticate(self.business)
        url = reverse('offerdetail-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OfferRetrieveTests(APITestCase):

    def setUp(self):
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.customer = create_user_with_profile('cus', UserProfile.CUSTOMER)
        self.offer = create_full_offer(self.business)
        self.url = reverse('offer-detail', kwargs={'pk': self.offer.id})

    def test_get_offer_returns_details_and_min_values(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.business.id)
        self.assertEqual(len(response.data['details']), 3)
        self.assertEqual(response.data['min_price'], 100)
        self.assertEqual(response.data['min_delivery_time'], 5)
        self.assertNotIn('user_details', response.data)

    def test_get_offer_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_unknown_offer_returns_404(self):
        self.client.force_authenticate(self.customer)
        url = reverse('offer-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class OfferUpdateTests(APITestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.other = create_user_with_profile('other', UserProfile.BUSINESS)
        self.offer = create_full_offer(self.business)
        self.url = reverse('offer-detail', kwargs={'pk': self.offer.id})
        self.client.force_authenticate(self.business)

    def test_patch_title_only(self):
        response = self.client.patch(self.url, {'title': 'New'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New')
        self.assertEqual(len(response.data['details']), 3)

    def test_patch_single_detail_keeps_its_id(self):
        basic = self.offer.details.get(offer_type='basic')
        data = {'details': [{'price': 120, 'offer_type': 'basic'}]}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basic.refresh_from_db()
        self.assertEqual(basic.price, 120)
        self.assertEqual(basic.title, 'Basic')
        self.assertEqual(response.data['details'][0]['id'], basic.id)

    def test_patch_detail_without_offer_type_fails(self):
        data = {'details': [{'price': 120}]}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_detail_with_unknown_offer_type_fails(self):
        self.offer.details.filter(offer_type='premium').delete()
        data = {'details': [{'price': 1, 'offer_type': 'premium'}]}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_uploads_image(self):
        image = SimpleUploadedFile('a.png', b'img', content_type='image/png')
        response = self.client.patch(
            self.url, {'image': image}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('offer_images/a', response.data['image'])

    def test_patch_by_other_user_is_forbidden(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(self.url, {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url, {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_unknown_offer_returns_404(self):
        url = reverse('offer-detail', kwargs={'pk': 9999})
        response = self.client.patch(url, {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.url, OFFER_DATA, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class OfferDeleteTests(APITestCase):

    def setUp(self):
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.other = create_user_with_profile('other', UserProfile.BUSINESS)
        self.offer = create_full_offer(self.business)
        self.url = reverse('offer-detail', kwargs={'pk': self.offer.id})

    def test_owner_can_delete_offer_and_details(self):
        self.client.force_authenticate(self.business)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())

    def test_other_user_cannot_delete_offer(self):
        self.client.force_authenticate(self.other)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.exists())

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unknown_offer_returns_404(self):
        self.client.force_authenticate(self.business)
        url = reverse('offer-detail', kwargs={'pk': 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
