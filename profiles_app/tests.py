import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import UserProfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def create_user_with_profile(username, profile_type):
    """Small helper so every test can create users in one line."""
    user = User.objects.create_user(username, f'{username}@mail.de', 'pw')
    UserProfile.objects.create(user=user, type=profile_type)
    return user


class UserProfileModelTests(APITestCase):

    def test_str_shows_username_and_type(self):
        user = create_user_with_profile('max', UserProfile.BUSINESS)
        self.assertEqual(str(user.profile), 'max (business)')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfileDetailTests(APITestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = create_user_with_profile('owner', UserProfile.BUSINESS)
        self.other = create_user_with_profile('other', UserProfile.CUSTOMER)
        self.url = reverse('profile-detail', kwargs={'pk': self.user.id})
        self.client.force_authenticate(self.user)

    def test_get_profile_returns_all_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['username'], 'owner')
        self.assertEqual(response.data['email'], 'owner@mail.de')
        self.assertEqual(response.data['type'], 'business')

    def test_empty_fields_are_empty_strings_not_null(self):
        response = self.client.get(self.url)
        for field in ['first_name', 'last_name', 'location', 'tel',
                      'description', 'working_hours']:
            self.assertEqual(response.data[field], '')

    def test_get_profile_of_other_user_is_allowed(self):
        url = reverse('profile-detail', kwargs={'pk': self.other.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_unknown_profile_returns_404(self):
        url = reverse('profile-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_updates_profile_and_user_fields(self):
        data = {'first_name': 'Max', 'location': 'Berlin',
                'email': 'new@mail.de'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Max')
        self.assertEqual(self.user.email, 'new@mail.de')
        self.assertEqual(self.user.profile.location, 'Berlin')

    def test_patch_uploads_profile_picture(self):
        image = SimpleUploadedFile('me.png', b'img', content_type='image/png')
        response = self.client.patch(
            self.url, {'file': image}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_pictures/me', response.data['file'])

    def test_patch_cannot_change_type(self):
        response = self.client.patch(
            self.url, {'type': 'customer'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'business')

    def test_patch_fails_if_email_is_taken(self):
        data = {'email': 'other@mail.de'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_profile_of_other_user_is_forbidden(self):
        url = reverse('profile-detail', kwargs={'pk': self.other.id})
        response = self.client.patch(url, {'tel': '123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url, {'tel': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.url, {}, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class ProfileListTests(APITestCase):

    def setUp(self):
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.customer = create_user_with_profile('cus', UserProfile.CUSTOMER)
        self.client.force_authenticate(self.customer)

    def get_usernames(self, url_name):
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [profile['username'] for profile in response.data]

    def test_business_list_contains_only_business_users(self):
        usernames = self.get_usernames('business-profile-list')
        self.assertIn('biz', usernames)
        self.assertNotIn('cus', usernames)

    def test_customer_list_contains_only_customers(self):
        usernames = self.get_usernames('customer-profile-list')
        self.assertIn('cus', usernames)
        self.assertNotIn('biz', usernames)

    def test_customer_list_has_uploaded_at(self):
        response = self.client.get(reverse('customer-profile-list'))
        self.assertIn('uploaded_at', response.data[0])

    def test_lists_require_authentication(self):
        self.client.force_authenticate(None)
        for url_name in ['business-profile-list', 'customer-profile-list']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )
