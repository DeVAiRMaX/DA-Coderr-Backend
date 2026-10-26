from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer
from profiles_app.models import UserProfile
from reviews_app.models import Review


def create_user_with_profile(username, profile_type):
    user = User.objects.create_user(username, f'{username}@mail.de', 'pw')
    UserProfile.objects.create(user=user, type=profile_type)
    return user


class BaseInfoTests(APITestCase):

    def setUp(self):
        self.url = reverse('base-info')
        # The guest users from the data migration are already in the test
        # database, so the counts start from the existing data
        self.business_count = UserProfile.objects.filter(
            type=UserProfile.BUSINESS
        ).count()

    def test_base_info_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_average_rating_is_zero_without_reviews(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['review_count'], 0)
        self.assertEqual(response.data['average_rating'], 0)

    def test_base_info_counts_reviews_profiles_and_offers(self):
        business = create_user_with_profile('biz', UserProfile.BUSINESS)
        Offer.objects.create(user=business, title='Logo')
        Offer.objects.create(user=business, title='Website')
        for number, rating in enumerate([5, 4, 4]):
            reviewer = create_user_with_profile(
                f'cus{number}', UserProfile.CUSTOMER
            )
            Review.objects.create(
                business_user=business, reviewer=reviewer, rating=rating
            )
        response = self.client.get(self.url)
        self.assertEqual(response.data['review_count'], 3)
        self.assertEqual(response.data['average_rating'], 4.3)
        self.assertEqual(
            response.data['business_profile_count'], self.business_count + 1
        )
        self.assertEqual(response.data['offer_count'], 2)
