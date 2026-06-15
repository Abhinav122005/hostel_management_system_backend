from django.db import transaction
from django.db.models import Avg
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from hostels_app.models import Hostel
from .models import Review, UserReview
from .serializers import ReviewCreateSerializer, ReviewSerializer, UserReviewCreateSerializer, UserReviewSerializer

def _update_hostel_rating(hostel_id):
    avg_rating = Review.objects.filter(hostel_id=hostel_id).aggregate(Avg("rating"))["rating__avg"]
    if avg_rating is not None:
        Hostel.objects.filter(id=hostel_id).update(rating=round(avg_rating, 1))
    else:
        Hostel.objects.filter(id=hostel_id).update(rating=0)

# """
# Expected JSON Payload:
# {
#   "userId": 1,
#   "hostelId": 1,
#   "rating": 4.5,
#   "comment": "Great place!"
# }
# """
@api_view(["POST"])
def add_review(request):
    serializer = ReviewCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            review = serializer.save()
            _update_hostel_rating(review.hostel_id)
            
        return Response(
            {
                "message": "Review added successfully",
                "review": ReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_hostel_reviews(request, hostel_id):
    reviews = Review.objects.filter(hostel_id=hostel_id).select_related("user")
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        hostel_id = review.hostel_id
        with transaction.atomic():
            review.delete()
            _update_hostel_rating(hostel_id)
        return Response({"message": "Review deleted successfully"}, status=status.HTTP_200_OK)
    except Review.DoesNotExist:
        return Response({"message": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

# """
# Expected JSON Payload:
# {
#   "ownerId": 1,
#   "userId": 1,
#   "rating": 5.0,
#   "comment": "Good tenant!"
# }
# """
@api_view(["POST"])
def add_user_review(request):
    serializer = UserReviewCreateSerializer(data=request.data)
    if serializer.is_valid():
        review = serializer.save()
        return Response(
            {
                "message": "User review added successfully",
                "review": UserReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_user_reviews(request, user_id):
    reviews = UserReview.objects.filter(user_id=user_id).select_related("owner")
    serializer = UserReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_user_review(request, review_id):
    try:
        review = UserReview.objects.get(id=review_id)
        review.delete()
        return Response({"message": "User review deleted successfully"}, status=status.HTTP_200_OK)
    except UserReview.DoesNotExist:
        return Response({"message": "User review not found"}, status=status.HTTP_404_NOT_FOUND)
