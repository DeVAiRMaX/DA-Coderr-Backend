from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profiles_app.models import UserProfile
from .models import Review


def create_user_with_profile(username, profile_type):
    user = User.objects.create_user(username, f'{username}@mail.de', 'pw')
    UserProfile.objects.create(user=user, type=profile_type)
    return user


class ReviewTestCase(APITestCase):
    """Creates the users that every review test needs."""

    def setUp(self):
        self.customer = create_user_with_profile('cus', UserProfile.CUSTOMER)
        self.other_customer = create_user_with_profile(
            'cus2', UserProfile.CUSTOMER
        )
        self.business = create_user_with_profile('biz', UserProfile.BUSINESS)
        self.other_business = create_user_with_profile(
            'biz2', UserProfile.BUSINESS
        )

    def create_review(self, reviewer, business_user, rating=4):
        return Review.objects.create(
            reviewer=reviewer, business_user=business_user, rating=rating,
            description='Sehr gut',
        )


class ReviewModelTests(ReviewTestCase):

    def test_str_shows_users_and_rating(self):
        review = self.create_review(self.customer, self.business, rating=5)
        self.assertEqual(str(review), 'cus -> biz: 5')


class ReviewListTests(ReviewTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('review-list')
        self.create_review(self.customer, self.business, rating=5)
        self.create_review(self.customer, self.other_business, rating=2)
        self.create_review(self.other_customer, self.business, rating=3)
        self.client.force_authenticate(self.business)

    def get_ratings(self, query=''):
        response = self.client.get(f'{self.url}?{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [review['rating'] for review in response.data]

    def test_list_returns_all_reviews_newest_first(self):
        self.assertEqual(self.get_ratings(), [3, 2, 5])

    def test_filter_by_business_user(self):
        ratings = self.get_ratings(f'business_user_id={self.business.id}')
        self.assertCountEqual(ratings, [5, 3])

    def test_filter_by_reviewer(self):
        ratings = self.get_ratings(f'reviewer_id={self.customer.id}')
        self.assertCountEqual(ratings, [5, 2])

    def test_ordering_by_rating(self):
        self.assertEqual(self.get_ratings('ordering=rating'), [2, 3, 5])
        self.assertEqual(self.get_ratings('ordering=-rating'), [5, 3, 2])

    def test_ordering_by_updated_at(self):
        self.assertEqual(self.get_ratings('ordering=updated_at'), [5, 2, 3])

    def test_empty_query_params_are_ignored(self):
        query = 'business_user_id=&reviewer_id=&ordering='
        self.assertEqual(len(self.get_ratings(query)), 3)

    def test_list_contains_all_fields(self):
        review = self.client.get(self.url).data[0]
        for field in ['id', 'business_user', 'reviewer', 'rating',
                      'description', 'created_at', 'updated_at']:
            self.assertIn(field, review)

    def test_list_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReviewCreateTests(ReviewTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('review-list')
        self.data = {
            'business_user': self.business.id,
            'rating': 4,
            'description': 'Alles war toll!',
        }
        self.client.force_authenticate(self.customer)

    def test_customer_can_create_review(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.customer.id)
        self.assertEqual(response.data['business_user'], self.business.id)
        self.assertEqual(Review.objects.count(), 1)

    def test_reviewer_cannot_be_set_by_client(self):
        self.data['reviewer'] = self.other_customer.id
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.data['reviewer'], self.customer.id)

    def test_second_review_for_same_business_user_is_forbidden(self):
        self.create_review(self.customer, self.business)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.count(), 1)

    def test_business_user_cannot_create_review(self):
        self.client.force_authenticate(self.other_business)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_review_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_be_reviewed(self):
        self.data['business_user'] = self.other_customer.id
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_must_be_between_one_and_five(self):
        for rating in [0, 6]:
            self.data['rating'] = rating
            response = self.client.post(self.url, self.data, format='json')
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )

    def test_missing_fields_return_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewUpdateDeleteTests(ReviewTestCase):

    def setUp(self):
        super().setUp()
        self.review = self.create_review(self.customer, self.business)
        self.url = reverse('review-detail', kwargs={'pk': self.review.id})
        self.client.force_authenticate(self.customer)

    def test_reviewer_can_update_rating_and_description(self):
        data = {'rating': 5, 'description': 'Noch besser als erwartet!'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.description, data['description'])

    def test_other_fields_cannot_be_changed(self):
        data = {'business_user': self.other_business.id}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.review.refresh_from_db()
        self.assertEqual(self.review.business_user, self.business)

    def test_invalid_rating_returns_400(self):
        response = self.client.patch(self.url, {'rating': 9}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_update_review(self):
        self.client.force_authenticate(self.other_customer)
        response = self.client.patch(self.url, {'rating': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url, {'rating': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_unknown_review_returns_404(self):
        url = reverse('review-detail', kwargs={'pk': 9999})
        response = self.client.patch(url, {'rating': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reviewer_can_delete_review(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.exists())

    def test_other_user_cannot_delete_review(self):
        self.client.force_authenticate(self.business)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.exists())

    def test_delete_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unknown_review_returns_404(self):
        url = reverse('review-detail', kwargs={'pk': 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
