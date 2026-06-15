from rest_framework import serializers
from .models import Review, UserReview
from users.models import User
from hostels_app.models import Hostel
from owners.models import Owner

class ReviewSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    hostelId = serializers.IntegerField(source="hostel_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("_id", "userId", "hostelId", "rating", "comment", "createdAt", "updatedAt", "user")
        
    def get_user(self, obj):
        return {
            "_id": obj.user.id,
            "name": obj.user.name,
            "email": obj.user.email,
        }

class ReviewCreateSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    hostelId = serializers.IntegerField()
    rating = serializers.FloatField()
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def validate_hostelId(self, value):
        if not Hostel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Hostel not found")
        return value

    def validate_rating(self, value):
        if not (0 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 0 and 5")
        return value

    def create(self, validated_data):
        # We need to handle the unique_together constraint by updating if it exists
        user_id = validated_data["userId"]
        hostel_id = validated_data["hostelId"]
        
        review, created = Review.objects.update_or_create(
            user_id=user_id,
            hostel_id=hostel_id,
            defaults={
                "rating": validated_data["rating"],
                "comment": validated_data.get("comment", "")
            }
        )
        return review

class UserReviewSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    ownerId = serializers.IntegerField(source="owner_id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    owner = serializers.SerializerMethodField()

    class Meta:
        model = UserReview
        fields = ("_id", "ownerId", "userId", "rating", "comment", "createdAt", "updatedAt", "owner")
        
    def get_owner(self, obj):
        return {
            "_id": obj.owner.id,
            "name": obj.owner.name,
            "email": obj.owner.email,
        }

class UserReviewCreateSerializer(serializers.Serializer):
    ownerId = serializers.IntegerField()
    userId = serializers.IntegerField()
    rating = serializers.FloatField()
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_ownerId(self, value):
        if not Owner.objects.filter(id=value).exists():
            raise serializers.ValidationError("Owner not found")
        return value

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def validate_rating(self, value):
        if not (0 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 0 and 5")
        return value

    def create(self, validated_data):
        owner_id = validated_data["ownerId"]
        user_id = validated_data["userId"]
        
        review, created = UserReview.objects.update_or_create(
            owner_id=owner_id,
            user_id=user_id,
            defaults={
                "rating": validated_data["rating"],
                "comment": validated_data.get("comment", "")
            }
        )
        return review
