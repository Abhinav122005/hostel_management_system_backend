from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer

# API Endpoint for getting all notifications for a specific user.
@api_view(['GET'])
def get_user_notifications(request, user_id):
    notifications = Notification.objects.filter(user_id=user_id, recipient_type='user').order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'count': notifications.count(),
        'notifications': serializer.data
    }, status=status.HTTP_200_OK)

# API Endpoint for getting all notifications for a specific owner.
@api_view(['GET'])
def get_owner_notifications(request, owner_id):
    notifications = Notification.objects.filter(owner_id=owner_id, recipient_type='owner').order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'count': notifications.count(),
        'notifications': serializer.data
    }, status=status.HTTP_200_OK)

# API Endpoint to create a notification directly.
# """
# Expected JSON Payload:
# {
#   "recipient_type": "user",
#   "user": 1,
#   "type": "chat",
#   "message": "You have a new message",
#   "data": {"conversationId": 1}
# }
# """
@api_view(['POST'])
def create_notification(request):
    serializer = NotificationCreateSerializer(data=request.data)
    if serializer.is_valid():
        notification = serializer.save()
        return Response({
            'message': 'Notification created',
            'notification': NotificationSerializer(notification).data
        }, status=status.HTTP_201_CREATED)
    return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# API Endpoint to mark a notification as read.
# """
# Expected JSON Payload (optional, as it forces read=true):
# {
#   "read": true
# }
# """
@api_view(['PUT', 'PATCH'])
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.read = True
        notification.save(update_fields=['read'])
        return Response({
            'message': 'Notification marked as read',
            'notification': NotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({'message': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

# API Endpoint to delete a notification.
@api_view(['DELETE'])
def delete_notification(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.delete()
        return Response({'message': 'Notification deleted successfully'}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({'message': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
