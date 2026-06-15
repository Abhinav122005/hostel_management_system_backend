from rest_framework import serializers

from hostels_app.models import Hostel
from users.models import User

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    hostelId = serializers.IntegerField(source="hostel_id", read_only=True)
    sharingType = serializers.CharField(source="sharing_type", read_only=True)
    vacancyDeducted = serializers.BooleanField(source="vacancy_deducted", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "_id",
            "userId",
            "hostelId",
            "sharingType",
            "message",
            "status",
            "vacancyDeducted",
            "createdAt",
        )


class BookingCreateSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    hostelId = serializers.IntegerField()
    sharingType = serializers.CharField()
    message = serializers.CharField(required=False, allow_blank=True)

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def validate_hostelId(self, value):
        if not Hostel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Hostel not found")
        return value

    def create(self, validated_data):
        return Booking.objects.create(
            user_id=validated_data["userId"],
            hostel_id=validated_data["hostelId"],
            sharing_type=validated_data["sharingType"],
            message=validated_data.get("message", ""),
        )


class BookingStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending", "approved", "rejected"])

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.save(update_fields=["status"])
        return instance


class UserBookingSerializer(BookingSerializer):
    hostel = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ("hostel",)

    def get_hostel(self, obj):
        return {
            "_id": obj.hostel_id,
            "name": obj.hostel.name,
            "area": obj.hostel.area,
            "images": obj.hostel.images,
        }


class BookingDetailSerializer(BookingSerializer):
    user = serializers.SerializerMethodField()
    hostel = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ("user", "hostel")

    def get_user(self, obj):
        return {
            "_id": obj.user_id,
            "name": obj.user.name,
            "email": obj.user.email,
        }

    def get_hostel(self, obj):
        return {
            "_id": obj.hostel_id,
            "name": obj.hostel.name,
            "area": obj.hostel.area,
            "vacancy": obj.hostel.vacancy,
        }
