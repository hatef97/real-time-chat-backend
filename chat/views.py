from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from .models import ChatRoom, Message, ChatParticipant
from .serializers import ChatRoomSerializer, MessageSerializer, ChatParticipantSerializer
from core.models import User



class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing, creating, and listing chat rooms.
    """
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Restrict chat rooms to those where the user is a participant.
        """
        return ChatRoom.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """
        Ensure that the authenticated user is added as a participant when creating a new chat room.
        """
        chat_room = serializer.save()
        chat_room.participants.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Custom action to add a participant to the chat room.
        """
        chat_room = self.get_object()
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        chat_room.participants.add(user)
        return Response({"detail": f"{username} added to chat room."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """
        Custom action to remove a participant from the chat room.
        """
        chat_room = self.get_object()
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        chat_room.participants.remove(user)
        return Response({"detail": f"{username} removed from chat room."}, status=status.HTTP_200_OK)



class MessageViewSet(viewsets.ModelViewSet):
    """
    A viewset for creating and listing messages in a chat room.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter messages by chat room and ensure that the user is a participant.
        """
        chat_room_id = self.kwargs.get('chat_room_id')
        chat_room = ChatRoom.objects.get(id=chat_room_id)
        if self.request.user not in chat_room.participants.all():
            return Message.objects.none()  # User is not a participant
        return Message.objects.filter(chat_room=chat_room)

    def perform_create(self, serializer):
        """
        Automatically associate the message with the authenticated user.
        """
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['get'])
    def chat_messages(self, request, pk=None):
        """
        Custom action to get all messages from a specific chat room.
        """
        chat_room = self.get_object()
        messages = Message.objects.filter(chat_room=chat_room)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)



class ChatParticipantViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing chat participants.
    """
    queryset = ChatParticipant.objects.all()
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter to only return participants for the current authenticated user's chat rooms.
        """
        return ChatParticipant.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Ensure that the authenticated user is added as a participant when creating a new entry.
        """
        chat_room = serializer.validated_data['chat_room']
        serializer.save(user=self.request.user, chat_room=chat_room)

    @action(detail=True, methods=['post'])
    def deactivate_participant(self, request, pk=None):
        """
        Custom action to deactivate a participant (making them inactive).
        """
        chat_participant = self.get_object()
        chat_participant.is_active = False
        chat_participant.save()
        return Response({"detail": "Participant deactivated."}, status=status.HTTP_200_OK)
        
