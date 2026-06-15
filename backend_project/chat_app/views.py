from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, MessageCreateSerializer
from users.models import User
from owners.models import Owner

# API Endpoint for listing all conversations or creating a new one.
# GET: Fetch conversations. Optional query params: `userId`, `ownerId`
# POST: Create a new conversation or retrieve an existing one between a specific user and owner.
@api_view(["GET", "POST"])
def conversation_list(request):
    if request.method == "GET":
        user_id = request.query_params.get("userId")
        owner_id = request.query_params.get("ownerId")
        
        conversations = Conversation.objects.all()
        if user_id:
            conversations = conversations.filter(user_id=user_id)
        if owner_id:
            conversations = conversations.filter(owner_id=owner_id)
            
        conversations = conversations.select_related("user", "owner").prefetch_related("messages")
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == "POST":
        # Create or get conversation
        user_id = request.data.get("userId")
        owner_id = request.data.get("ownerId")
        
        if not user_id or not owner_id:
            return Response({"message": "userId and ownerId are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(id=user_id)
            owner = Owner.objects.get(id=owner_id)
        except (User.DoesNotExist, Owner.DoesNotExist):
            return Response({"message": "Invalid user or owner"}, status=status.HTTP_400_BAD_REQUEST)
            
        conversation, created = Conversation.objects.get_or_create(user=user, owner=owner)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# API Endpoint for getting messages of a conversation or sending a new message.
# GET: Fetch all messages for a specific conversation ID.
# POST: Send a new message to the conversation. Requires `senderType` and `content`.
@api_view(["GET", "POST"])
def message_list(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({"message": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == "POST":
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                message = Message.objects.create(
                    conversation=conversation,
                    sender_type=serializer.validated_data["senderType"],
                    content=serializer.validated_data["content"]
                )
                # Update conversation updated_at
                conversation.save()
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
