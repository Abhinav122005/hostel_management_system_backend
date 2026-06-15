from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['user', 'owner', 'recipient_type', 'type', 'message', 'data']
        
    def validate(self, attrs):
        recipient_type = attrs.get('recipient_type')
        if recipient_type == 'user' and not attrs.get('user'):
            raise serializers.ValidationError({"user": "User is required when recipient_type is 'user'"})
        if recipient_type == 'owner' and not attrs.get('owner'):
            raise serializers.ValidationError({"owner": "Owner is required when recipient_type is 'owner'"})
        return attrs
