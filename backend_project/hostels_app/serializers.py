from rest_framework import serializers

from owners.models import Owner
from users.serializers import UserSerializer

from .models import Hostel


SHARING_KEY_MAP = {
    "2": "twoSharing",
    "3": "threeSharing",
    "4": "fourSharing",
    "5": "fiveSharing",
    "6": "sixSharing",
}

DEFAULT_SHARING = {
    "twoSharing": 0,
    "threeSharing": 0,
    "fourSharing": 0,
    "fiveSharing": 0,
    "sixSharing": 0,
}


def map_sharing_data(data=None):
    output = DEFAULT_SHARING.copy()
    for key, value in (data or {}).items():
        mapped_key = SHARING_KEY_MAP.get(str(key), key)
        if mapped_key in output:
            output[mapped_key] = int(value or 0)
    return output


class HostelSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    ownerId = serializers.IntegerField(source="owner_id", read_only=True)
    roomSharing = serializers.JSONField(source="room_sharing", read_only=True)
    sharingMedia = serializers.JSONField(source="sharing_media", read_only=True)
    sharingImages = serializers.JSONField(source="sharing_images", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Hostel
        fields = (
            "_id",
            "name",
            "area",
            "address",
            "description",
            "distance",
            "rating",
            "ownerId",
            "type",
            "images",
            "videos",
            "sharingMedia",
            "sharingImages",
            "roomSharing",
            "vacancy",
            "location",
            "createdAt",
        )

    def get_location(self, obj):
        return {
            "type": "Point",
            "coordinates": [obj.longitude, obj.latitude],
        }


class HostelWithUsersSerializer(HostelSerializer):
    hostelUsers = UserSerializer(source="hostel_users", many=True, read_only=True)

    class Meta(HostelSerializer.Meta):
        fields = HostelSerializer.Meta.fields + ("hostelUsers",)


class HostelCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    area = serializers.CharField()
    address = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    distance = serializers.FloatField(required=False, allow_null=True)
    ownerId = serializers.IntegerField()
    type = serializers.ChoiceField(choices=["boys", "girls", "room"], required=False, allow_blank=True)
    roomSharing = serializers.JSONField(required=False)
    vacancy = serializers.JSONField(required=False)
    location = serializers.JSONField(required=False)
    images = serializers.JSONField(required=False)
    videos = serializers.JSONField(required=False)
    sharingMedia = serializers.JSONField(required=False)

    def validate_ownerId(self, value):
        owner = Owner.objects.filter(id=value).first()
        if not owner:
            raise serializers.ValidationError("Owner not found")
        return value

    def create(self, validated_data):
        location = validated_data.get("location") or {}
        coordinates = location.get("coordinates") or [0, 0]
        if len(coordinates) < 2:
            coordinates = [0, 0]

        return Hostel.objects.create(
            name=validated_data["name"],
            area=validated_data["area"],
            address=validated_data.get("address", ""),
            description=validated_data.get("description", ""),
            distance=validated_data.get("distance"),
            owner_id=validated_data["ownerId"],
            type=(validated_data.get("type") or "").lower(),
            images=validated_data.get("images", []),
            videos=validated_data.get("videos", []),
            sharing_media=validated_data.get("sharingMedia", {}),
            room_sharing=map_sharing_data(validated_data.get("roomSharing")),
            vacancy=map_sharing_data(validated_data.get("vacancy")),
            longitude=float(coordinates[0] or 0),
            latitude=float(coordinates[1] or 0),
        )


class VacancySerializer(serializers.Serializer):
    sharingKey = serializers.CharField()
