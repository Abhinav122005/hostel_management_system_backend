from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from users.models import User

from .models import HostelRequest
from .serializers import (
    HostelRequestCreateSerializer,
    HostelRequestSerializer,
    OwnerRequestSerializer,
    RequestStatusSerializer,
    UserRequestSerializer,
    UserSearchSerializer,
)


@api_view(["GET"])
def search_users(request):
    query = (request.query_params.get("query") or "").strip()
    if not query:
        return Response({"message": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

    users = User.objects.filter(email__icontains=query) | User.objects.filter(mobile__icontains=query)
    users = users.distinct()
    serializer = UserSearchSerializer(users, many=True)
    return Response({"count": users.count(), "data": serializer.data}, status=status.HTTP_200_OK)


# """
# Expected JSON Payload:
# {
#   "userId": 1,
#   "hostelId": 1,
#   "ownerId": 1,
#   "senderType": "user",
#   "sharingType": "2-sharing",
#   "sharingPrice": 2500
# }
# """
@api_view(["POST"])
def send_request(request):
    serializer = HostelRequestCreateSerializer(data=request.data)
    if serializer.is_valid():
        hostel_request = serializer.save()
        return Response(
            {
                "message": f"{hostel_request.sender_type} request sent successfully",
                "data": HostelRequestSerializer(hostel_request).data,
            },
            status=status.HTTP_201_CREATED,
        )

    errors = serializer.errors.get("non_field_errors")
    message = errors[0] if errors else serializer.errors
    status_code = status.HTTP_404_NOT_FOUND if message in ["User not found", "Hostel not found", "Owner not found"] else status.HTTP_400_BAD_REQUEST
    return Response({"message": message}, status=status_code)


@api_view(["GET"])
def get_user_requests(request, user_id):
    requests = HostelRequest.objects.filter(user_id=user_id).select_related("owner", "hostel")
    serializer = UserRequestSerializer(requests, many=True)
    return Response({"count": requests.count(), "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_owner_requests(request, owner_id):
    requests = HostelRequest.objects.filter(owner_id=owner_id).select_related("user", "hostel", "hostel__owner")
    serializer = OwnerRequestSerializer(requests, many=True)
    return Response({"count": requests.count(), "data": serializer.data}, status=status.HTTP_200_OK)


def _decrease_vacancy(hostel_request):
    hostel = hostel_request.hostel
    sharing_type = hostel_request.sharing_type
    vacancy = hostel.vacancy or {}

    if sharing_type not in vacancy:
        return "Invalid sharing type"

    current_vacancy = int(vacancy.get(sharing_type, 0) or 0)
    if current_vacancy <= 0:
        return f"{sharing_type} rooms are full"

    vacancy[sharing_type] = current_vacancy - 1
    hostel.vacancy = vacancy
    hostel.save(update_fields=["vacancy"])
    return None


def _restore_vacancy(hostel_request):
    hostel = hostel_request.hostel
    sharing_type = hostel_request.sharing_type
    vacancy = hostel.vacancy or {}
    vacancy[sharing_type] = int(vacancy.get(sharing_type, 0) or 0) + 1
    hostel.vacancy = vacancy
    hostel.save(update_fields=["vacancy"])


def _set_user_joined_hostel(hostel_request):
    user = hostel_request.user
    hostel = hostel_request.hostel
    sharing_price = hostel_request.sharing_price
    if sharing_price is None:
        sharing_price = (hostel.room_sharing or {}).get(hostel_request.sharing_type, 0)

    user.joined_hostel_id = str(hostel.id)
    user.joined_hostel_name = hostel.name
    user.joined_owner_id = str(hostel.owner_id)
    user.joined_sharing_type = hostel_request.sharing_type
    user.joined_sharing_price = sharing_price or 0
    from django.utils import timezone
    user.joined_date = timezone.now()
    user.save(
        update_fields=[
            "joined_hostel_id",
            "joined_hostel_name",
            "joined_owner_id",
            "joined_sharing_type",
            "joined_sharing_price",
            "joined_date",
            "updated_at",
        ]
    )


def _clear_user_joined_hostel(hostel_request):
    user = hostel_request.user
    user.joined_hostel_id = None
    user.joined_hostel_name = ""
    user.joined_owner_id = None
    user.joined_sharing_type = ""
    user.joined_sharing_price = None
    user.joined_date = None
    user.save(
        update_fields=[
            "joined_hostel_id",
            "joined_hostel_name",
            "joined_owner_id",
            "joined_sharing_type",
            "joined_sharing_price",
            "joined_date",
            "updated_at",
        ]
    )


# """
# Expected JSON Payload:
# {
#   "status": "accepted"
# }
# """
@api_view(["PUT", "PATCH", "POST"])
def update_request_status(request, request_id):
    serializer = RequestStatusSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "message": "Invalid status",
                "allowedStatuses": ["pending", "accepted", "declined"],
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_status = serializer.validated_data["status"]
    hostel_request = HostelRequest.objects.select_related("user", "hostel", "owner").filter(id=request_id).first()
    if not hostel_request:
        return Response({"message": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        hostel_request = HostelRequest.objects.select_for_update().select_related("user", "hostel", "owner").get(id=request_id)

        if new_status == "accepted" and not hostel_request.vacancy_deducted:
            vacancy_error = _decrease_vacancy(hostel_request)
            if vacancy_error:
                return Response({"message": vacancy_error}, status=status.HTTP_400_BAD_REQUEST)
            hostel_request.hostel.hostel_users.add(hostel_request.user)
            _set_user_joined_hostel(hostel_request)
            hostel_request.vacancy_deducted = True

        if new_status != "accepted" and hostel_request.vacancy_deducted:
            _restore_vacancy(hostel_request)
            hostel_request.hostel.hostel_users.remove(hostel_request.user)
            _clear_user_joined_hostel(hostel_request)
            hostel_request.vacancy_deducted = False

        hostel_request.status = new_status
        hostel_request.save(update_fields=["status", "vacancy_deducted"])

    hostel_request = HostelRequest.objects.select_related("user", "hostel", "owner").get(id=request_id)
    return Response(
        {
            "message": f"Request {hostel_request.status} successfully",
            "data": HostelRequestSerializer(hostel_request).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_joined_hostel(request, user_id):
    hostel_request = HostelRequest.objects.filter(user_id=user_id, status="accepted").select_related("hostel", "owner").first()
    if not hostel_request:
        return Response({"message": "User has not joined any hostel yet"}, status=status.HTTP_404_NOT_FOUND)

    hostel = hostel_request.hostel
    owner = hostel_request.owner
    return Response(
        {
            "hostel": {
                "id": hostel.id,
                "name": hostel.name,
                "area": hostel.area,
                "description": hostel.description,
                "images": hostel.images,
                "roomSharing": hostel.room_sharing,
                "vacancy": hostel.vacancy,
            },
            "owner": {
                "id": owner.id,
                "name": owner.name,
                "email": owner.email,
                "mobile": owner.mobile,
            },
            "sharingType": hostel_request.sharing_type,
        },
        status=status.HTTP_200_OK,
    )
