from rest_framework import serializers
from .models import Conversation, Message
from users.models import User
from owners.models import Owner

class MessageSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    senderType = serializers.CharField(source="sender_type")
    isRead = serializers.BooleanField(source="is_read")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Message
        fields = ("_id", "senderType", "content", "isRead", "createdAt")

class ConversationSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    userId = serializers.IntegerField(source="user_id", read_only=True)
    ownerId = serializers.IntegerField(source="owner_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    
    user = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("_id", "userId", "ownerId", "user", "owner", "lastMessage", "createdAt", "updatedAt")
        
    def get_user(self, obj):
        return {
            "_id": obj.user.id,
            "name": obj.user.name,
            "email": obj.user.email,
        }

    def get_owner(self, obj):
        return {
            "_id": obj.owner.id,
            "name": obj.owner.name,
            "email": obj.owner.email,
        }

    def get_lastMessage(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None

class MessageCreateSerializer(serializers.Serializer):
    senderType = serializers.ChoiceField(choices=["USER", "OWNER"])
    content = serializers.CharField()
