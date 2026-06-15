from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Booking
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingSerializer,
    BookingStatusSerializer,
    UserBookingSerializer,
)


SHARING_TO_VACANCY_KEY = {
    "1-sharing": "oneSharing",
    "2-sharing": "twoSharing",
    "3-sharing": "threeSharing",
    "4-sharing": "fourSharing",
    "5-sharing": "fiveSharing",
    "6-sharing": "sixSharing",
    "oneSharing": "oneSharing",
    "twoSharing": "twoSharing",
    "threeSharing": "threeSharing",
    "fourSharing": "fourSharing",
    "fiveSharing": "fiveSharing",
    "sixSharing": "sixSharing",
}


# """
# Expected JSON Payload:
# {
#   "userId": 1,
#   "hostelId": 1,
#   "sharingType": "2-sharing",
#   "price": 5000,
#   "bookingDate": "2024-01-01"
# }
# """
@api_view(["POST"])
def create_booking(request):
    serializer = BookingCreateSerializer(data=request.data)
    if serializer.is_valid():
        booking = serializer.save()
        return Response(
            {
                "message": "Booking request sent successfully",
                "booking": BookingSerializer(booking).data,
            },
            status=status.HTTP_201_CREATED,
        )

    if "hostelId" in serializer.errors:
        return Response({"message": "Hostel not found"}, status=status.HTTP_404_NOT_FOUND)
    if "userId" in serializer.errors:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Missing required fields", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_user_bookings(request, user_id):
    bookings = Booking.objects.filter(user_id=user_id).select_related("hostel")
    serializer = UserBookingSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_bookings(request):
    bookings = Booking.objects.select_related("user", "hostel").all()
    serializer = BookingDetailSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def _vacancy_key_for_booking(booking):
    return SHARING_TO_VACANCY_KEY.get(booking.sharing_type)


def _decrease_hostel_vacancy(booking):
    vacancy_key = _vacancy_key_for_booking(booking)
    if not vacancy_key:
        return "Invalid sharing type for vacancy"

    hostel = booking.hostel
    vacancy = hostel.vacancy or {}
    current_vacancy = int(vacancy.get(vacancy_key, 0) or 0)
    if current_vacancy <= 0:
        return "No vacancy available for this sharing type"

    vacancy[vacancy_key] = current_vacancy - 1
    hostel.vacancy = vacancy
    hostel.save(update_fields=["vacancy"])
    return None


def _restore_hostel_vacancy(booking):
    vacancy_key = _vacancy_key_for_booking(booking)
    if not vacancy_key:
        return

    hostel = booking.hostel
    vacancy = hostel.vacancy or {}
    vacancy[vacancy_key] = int(vacancy.get(vacancy_key, 0) or 0) + 1
    hostel.vacancy = vacancy
    hostel.save(update_fields=["vacancy"])


def _set_booking_status(booking_id, status_value):
    booking = Booking.objects.select_related("user", "hostel").filter(id=booking_id).first()
    if not booking:
        return Response({"message": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = BookingStatusSerializer(data={"status": status_value})
    if not serializer.is_valid():
        return Response(
            {
                "message": "Invalid status",
                "allowedStatuses": ["pending", "approved", "rejected"],
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_status = serializer.validated_data["status"]

    with transaction.atomic():
        booking = Booking.objects.select_for_update().select_related("user", "hostel").get(id=booking_id)

        if new_status == "approved" and not booking.vacancy_deducted:
            vacancy_error = _decrease_hostel_vacancy(booking)
            if vacancy_error:
                return Response({"message": vacancy_error}, status=status.HTTP_400_BAD_REQUEST)
            booking.vacancy_deducted = True

        if new_status != "approved" and booking.vacancy_deducted:
            _restore_hostel_vacancy(booking)
            booking.vacancy_deducted = False

        booking.status = new_status
        booking.save(update_fields=["status", "vacancy_deducted"])

    booking = Booking.objects.select_related("user", "hostel").get(id=booking_id)
    return Response(
        {
            "message": f"Booking status updated to {booking.status}",
            "booking": BookingDetailSerializer(booking).data,
        },
        status=status.HTTP_200_OK,
    )


# """
# Expected JSON Payload:
# {
#   "status": "approved"
# }
# """
@api_view(["PATCH", "POST"])
def update_booking_status(request, booking_id):
    return _set_booking_status(booking_id, request.data.get("status"))


@api_view(["POST"])
def approve_booking(request, booking_id):
    return _set_booking_status(booking_id, "approved")


@api_view(["POST"])
def reject_booking(request, booking_id):
    return _set_booking_status(booking_id, "rejected")
