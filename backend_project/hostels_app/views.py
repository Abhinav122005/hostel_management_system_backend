import json
import math
import time

from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from users.models import User

from .models import Hostel
from .serializers import (
    DEFAULT_SHARING,
    HostelCreateSerializer,
    HostelSerializer,
    HostelWithUsersSerializer,
    VacancySerializer,
)


def _save_uploaded_file(file_obj):
    filename = f"{int(time.time() * 1000)}-{file_obj.name}"
    saved_path = default_storage.save(filename, file_obj)
    return "/uploads/" + saved_path.replace("\\", "/")


def _hostel_payload(request):
    if request.data.get("hostel"):
        return json.loads(request.data["hostel"])
    return request.data.copy()


def _add_uploaded_media(request, payload):
    hostel_images = []
    hostel_videos = []
    sharing_media = {}

    for field_name, files in request.FILES.lists():
        for file_obj in files:
            file_path = _save_uploaded_file(file_obj)
            if field_name == "images":
                hostel_images.append(file_path)
            elif field_name == "videos":
                hostel_videos.append(file_path)
            elif field_name.startswith("sharing_"):
                parts = field_name.split("_")
                if len(parts) >= 3:
                    sharing_type = parts[1]
                    media_type = parts[2]
                    sharing_media.setdefault(sharing_type, {"images": [], "videos": []})
                    sharing_media[sharing_type].setdefault(media_type, []).append(file_path)

    if hostel_images:
        payload["images"] = hostel_images
    if hostel_videos:
        payload["videos"] = hostel_videos
    if sharing_media:
        payload["sharingMedia"] = sharing_media

    return payload


def _distance_meters(lat1, lng1, lat2, lng2):
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@api_view(["GET"])
def get_all_hostels(request):
    serializer = HostelSerializer(Hostel.objects.all(), many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_top_rated_hostels(request):
    limit = int(request.query_params.get("limit", 10))
    hostels = Hostel.objects.filter(rating__gte=4.5).order_by("-rating")[:limit]
    serializer = HostelSerializer(hostels, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_hostels_by_area(request):
    area = request.query_params.get("area")
    hostel_type = request.query_params.get("type")
    if not area:
        return Response({"message": "area query required"}, status=status.HTTP_400_BAD_REQUEST)

    hostels = Hostel.objects.filter(area__icontains=area)
    if hostel_type:
        hostels = hostels.filter(type=hostel_type.lower())

    serializer = HostelSerializer(hostels, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_single_hostel(request, hostel_id):
    hostel = Hostel.objects.filter(id=hostel_id).first()
    if not hostel:
        return Response({"message": "Hostel not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"data": HostelWithUsersSerializer(hostel).data}, status=status.HTTP_200_OK)


# """
# Expected JSON Payload (or Form-Data with "hostel" key):
# {
#   "hostel": "{\"name\": \"Sunny Hostel\", \"ownerId\": 1, \"area\": \"Downtown\"}"
# }
# """
@api_view(["POST"])
def add_hostel(request):
    payload = _add_uploaded_media(request, _hostel_payload(request))
    serializer = HostelCreateSerializer(data=payload)
    if serializer.is_valid():
        hostel = serializer.save()
        return Response(
            {
                "message": "Hostel created successfully",
                "data": HostelSerializer(hostel).data,
            },
            status=status.HTTP_201_CREATED,
        )

    if serializer.errors.get("ownerId"):
        return Response({"message": "Owner not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(
        {"message": "Failed to create hostel", "error": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
def filter_by_type(request):
    hostel_type = request.query_params.get("type")
    if not hostel_type:
        return Response({"message": "type query required"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = HostelSerializer(Hostel.objects.filter(type=hostel_type.lower()), many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def search_by_area_and_type(request):
    area = request.query_params.get("area")
    hostel_type = request.query_params.get("type")

    hostels = Hostel.objects.all()
    if area:
        hostels = hostels.filter(area__icontains=area)
    if hostel_type:
        hostels = hostels.filter(type=hostel_type.lower())

    serializer = HostelSerializer(hostels, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_nearby_hostels(request):
    lat = request.query_params.get("lat")
    lng = request.query_params.get("lng")
    radius = int(request.query_params.get("radius", 5000))

    if not lat or not lng:
        return Response({"message": "lat and lng query required"}, status=status.HTTP_400_BAD_REQUEST)

    lat = float(lat)
    lng = float(lng)
    nearby_ids = []
    for hostel in Hostel.objects.all():
        if _distance_meters(lat, lng, hostel.latitude, hostel.longitude) <= radius:
            nearby_ids.append(hostel.id)

    serializer = HostelSerializer(Hostel.objects.filter(id__in=nearby_ids), many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# """
# Expected JSON Payload:
# {
#   "sharingKey": "2-sharing"
# }
# """
@api_view(["POST"])
def decrement_vacancy(request, hostel_id):
    serializer = VacancySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"message": "sharingKey required"}, status=status.HTTP_400_BAD_REQUEST)

    hostel = Hostel.objects.filter(id=hostel_id).first()
    if not hostel:
        return Response({"message": "No vacancy or hostel not found"}, status=status.HTTP_400_BAD_REQUEST)

    sharing_key = serializer.validated_data["sharingKey"]
    vacancy = hostel.vacancy or DEFAULT_SHARING.copy()
    current_vacancy = int(vacancy.get(sharing_key, 0))
    if current_vacancy <= 0:
        return Response({"message": "No vacancy or hostel not found"}, status=status.HTTP_400_BAD_REQUEST)

    vacancy[sharing_key] = current_vacancy - 1
    hostel.vacancy = vacancy
    hostel.save(update_fields=["vacancy"])
    return Response(
        {"message": "Vacancy updated", "data": HostelSerializer(hostel).data},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_user_joined_hostel(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"message": "User not joined any hostel"}, status=status.HTTP_404_NOT_FOUND)

    hostel = Hostel.objects.filter(hostel_users=user).first()
    if not hostel:
        return Response({"message": "User not joined any hostel"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {"message": "User joined hostel found", "data": HostelSerializer(hostel).data},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_hostels_by_owner(request, owner_id):
    serializer = HostelSerializer(Hostel.objects.filter(owner_id=owner_id), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_hostels_with_users(request, owner_id):
    hostels = Hostel.objects.filter(owner_id=owner_id).prefetch_related("hostel_users")
    if not hostels.exists():
        return Response({"message": "No hostels found for this owner"}, status=status.HTTP_404_NOT_FOUND)

    serializer = HostelWithUsersSerializer(hostels, many=True)
    return Response(
        {
            "message": "Hostels with users fetched successfully",
            "hostels": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def get_hostel_by_id(request, hostel_id):
    hostel = Hostel.objects.filter(id=hostel_id).first()
    if not hostel:
        return Response({"message": "Hostel not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(HostelWithUsersSerializer(hostel).data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_hostel(request, hostel_id):
    hostel = Hostel.objects.filter(id=hostel_id).first()
    if not hostel:
        return Response({"message": "Hostel not found"}, status=status.HTTP_404_NOT_FOUND)

    hostel.delete()
    return Response(
        {"message": "Hostel and related reviews deleted successfully"},
        status=status.HTTP_200_OK,
    )
