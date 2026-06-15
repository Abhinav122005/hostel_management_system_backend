from rest_framework import serializers

from hostels_app.models import Hostel
from owners.models import Owner
from users.models import User

from .models import HostelRequest


class HostelRequestSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    ownerId = serializers.IntegerField(source="owner_id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    hostelId = serializers.IntegerField(source="hostel_id", read_only=True)
    senderType = serializers.CharField(source="sender_type", read_only=True)
    sharingType = serializers.CharField(source="sharing_type", read_only=True)
    sharingPrice = serializers.DecimalField(source="sharing_price", max_digits=10, decimal_places=2, read_only=True)
    vacancyDeducted = serializers.BooleanField(source="vacancy_deducted", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = HostelRequest
        fields = (
            "_id",
            "ownerId",
            "userId",
            "hostelId",
            "senderType",
            "status",
            "sharingPrice",
            "sharingType",
            "vacancyDeducted",
            "createdAt",
        )


class HostelRequestCreateSerializer(serializers.Serializer):
    ownerId = serializers.IntegerField(required=False)
    userId = serializers.IntegerField()
    hostelId = serializers.IntegerField()
    senderType = serializers.ChoiceField(choices=["owner", "user"])
    sharingType = serializers.CharField()
    sharingPrice = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    def validate(self, attrs):
        user_id = attrs.get("userId")
        hostel_id = attrs.get("hostelId")
        owner_id = attrs.get("ownerId")
        sender_type = attrs.get("senderType")

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise serializers.ValidationError("User not found")

        hostel = Hostel.objects.filter(id=hostel_id).first()
        if not hostel:
            raise serializers.ValidationError("Hostel not found")

        if sender_type == "user" and not owner_id:
            owner_id = hostel.owner_id
            attrs["ownerId"] = owner_id

        owner = Owner.objects.filter(id=owner_id).first()
        if not owner:
            raise serializers.ValidationError("Owner not found")

        already_joined = HostelRequest.objects.filter(user_id=user_id, status="accepted").exclude(hostel_id=hostel_id).first()
        if already_joined:
            raise serializers.ValidationError("User already joined another hostel! Cannot send request.")

        existing = HostelRequest.objects.filter(
            owner_id=owner_id,
            user_id=user_id,
            hostel_id=hostel_id,
            status__in=["pending", "accepted"],
        ).first()
        if existing:
            raise serializers.ValidationError(f"Request already {existing.status} between this owner and user")

        attrs["user"] = user
        attrs["hostel"] = hostel
        attrs["owner"] = owner
        return attrs

    def create(self, validated_data):
        return HostelRequest.objects.create(
            owner=validated_data["owner"],
            user=validated_data["user"],
            hostel=validated_data["hostel"],
            sender_type=validated_data["senderType"],
            sharing_type=validated_data["sharingType"],
            sharing_price=validated_data.get("sharingPrice"),
        )


class UserSearchSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = User
        fields = ("_id", "name", "email", "mobile", "createdAt")


class UserRequestSerializer(HostelRequestSerializer):
    owner = serializers.SerializerMethodField()
    hostel = serializers.SerializerMethodField()

    class Meta(HostelRequestSerializer.Meta):
        fields = HostelRequestSerializer.Meta.fields + ("owner", "hostel")

    def get_owner(self, obj):
        return {"_id": obj.owner_id, "name": obj.owner.name, "email": obj.owner.email}

    def get_hostel(self, obj):
        return {"_id": obj.hostel_id, "name": obj.hostel.name, "area": obj.hostel.area}


class OwnerRequestSerializer(HostelRequestSerializer):
    user = serializers.SerializerMethodField()
    hostel = serializers.SerializerMethodField()

    class Meta(HostelRequestSerializer.Meta):
        fields = HostelRequestSerializer.Meta.fields + ("user", "hostel")

    def get_user(self, obj):
        return {"_id": obj.user_id, "name": obj.user.name, "email": obj.user.email}

    def get_hostel(self, obj):
        return {
            "_id": obj.hostel_id,
            "name": obj.hostel.name,
            "area": obj.hostel.area,
            "ownerId": obj.hostel.owner_id,
        }


class RequestStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending", "accepted", "declined"])
