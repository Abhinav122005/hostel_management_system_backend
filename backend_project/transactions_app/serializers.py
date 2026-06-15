from rest_framework import serializers
from .models import Transaction
from users.models import User
from owners.models import Owner
from hostels_app.models import Hostel

class TransactionSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    ownerId = serializers.IntegerField(source="owner_id", read_only=True)
    hostelId = serializers.IntegerField(source="hostel_id", read_only=True)
    transactionId = serializers.CharField(source="transaction_id", read_only=True)
    paymentType = serializers.CharField(source="payment_type", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    user_info = serializers.SerializerMethodField()
    hostel_info = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "_id", "userId", "ownerId", "hostelId", "amount", "transactionId", 
            "paymentType", "status", "description", "createdAt", "updatedAt",
            "user_info", "hostel_info"
        )
        
    def get_user_info(self, obj):
        return {
            "name": obj.user.name,
            "email": obj.user.email,
        }
        
    def get_hostel_info(self, obj):
        return {
            "name": obj.hostel.name,
        }

class TransactionCreateSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    ownerId = serializers.IntegerField()
    hostelId = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paymentType = serializers.ChoiceField(choices=["rent", "booking", "deposit", "other"])
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def validate_ownerId(self, value):
        if not Owner.objects.filter(id=value).exists():
            raise serializers.ValidationError("Owner not found")
        return value

    def validate_hostelId(self, value):
        if not Hostel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Hostel not found")
        return value
