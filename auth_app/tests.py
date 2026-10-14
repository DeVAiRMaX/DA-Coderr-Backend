from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from profiles_app.models import UserProfile


class RegistrationTests(APITestCase):

    def setUp(self):
        self.url = reverse('registration')
        self.data = {
            'username': 'newuser',
            'email': 'newuser@mail.de',
            'password': 'secret123',
            'repeated_password': 'secret123',
            'type': 'business',
        }

    def test_registration_creates_user_profile_and_token(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.profile.type, UserProfile.BUSINESS)
        token = Token.objects.get(user=user)
        self.assertEqual(response.data['token'], token.key)
        self.assertEqual(response.data['user_id'], user.id)
        self.assertEqual(response.data['email'], 'newuser@mail.de')

    def test_registration_fails_if_passwords_differ(self):
        self.data['repeated_password'] = 'other'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_registration_fails_if_email_is_taken(self):
        User.objects.create_user('other', 'newuser@mail.de', 'pw')
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_fails_if_username_is_taken(self):
        User.objects.create_user('newuser', 'other@mail.de', 'pw')
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_registration_fails_with_invalid_type(self):
        self.data['type'] = 'admin'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', response.data)

    def test_registration_fails_without_data(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(
            'loginuser', 'login@mail.de', 'secret123'
        )

    def test_login_returns_token_and_user_data(self):
        data = {'username': 'loginuser', 'password': 'secret123'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data['token'], token.key)
        self.assertEqual(response.data['username'], 'loginuser')
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_fails_with_wrong_password(self):
        data = {'username': 'loginuser', 'password': 'wrong'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_fails_without_data(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GuestUserTests(APITestCase):
    """The guest users are created by a data migration."""

    def test_customer_guest_can_log_in(self):
        data = {'username': 'andrey', 'password': 'asdasd'}
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username='andrey')
        self.assertEqual(user.profile.type, UserProfile.CUSTOMER)

    def test_business_guest_can_log_in(self):
        data = {'username': 'kevin', 'password': 'asdasd24'}
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username='kevin')
        self.assertEqual(user.profile.type, UserProfile.BUSINESS)
