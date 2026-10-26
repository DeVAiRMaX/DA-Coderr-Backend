from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profiles_app.models import UserProfile
from reviews_app.models import Review


def get_average_rating():
    """Average of all ratings, rounded to one decimal (0 without reviews)."""
    average = Review.objects.aggregate(average=Avg('rating'))['average']
    if average is None:
        return 0
    return round(average, 1)


class BaseInfoView(APIView):
    """Public statistics about the platform for the start page."""

    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            'review_count': Review.objects.count(),
            'average_rating': get_average_rating(),
            'business_profile_count': UserProfile.objects.filter(
                type=UserProfile.BUSINESS
            ).count(),
            'offer_count': Offer.objects.count(),
        }
        return Response(data)
