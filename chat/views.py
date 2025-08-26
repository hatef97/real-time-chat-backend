from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import User
from .models import ChatRoom, Message, ChatParticipant
from .serializers import ChatRoomSerializer, MessageSerializer, ChatParticipantSerializer
from .permissions import IsRoomParticipant



class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    Only list/retrieve rooms the requester belongs to.
    On create, the creator is auto-added as a participant.
    Provides add_participant/remove_participant actions.
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated, IsRoomParticipant]

    def get_queryset(self):
        return (
            ChatRoom.objects
            .filter(participants=self.request.user)
            .prefetch_related("participants")
        )

    def perform_create(self, serializer):
        room = serializer.save()
        room.participants.add(self.request.user)

    @action(detail=True, methods=["post"])
    def add_participant(self, request, pk=None):
        room = self.get_object()  # permission ensures requester is a participant
        username = request.data.get("username")
        if not username:
            raise ValidationError({"username": "This field is required."})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError({"username": "User not found."})

        if room.participants.filter(id=user.id).exists():
            return Response({"detail": "User already in room."}, status=status.HTTP_200_OK)

        room.participants.add(user)
        return Response({"detail": f"{username} added."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def remove_participant(self, request, pk=None):
        room = self.get_object()  # requester must be a participant
        username = request.data.get("username")
        if not username:
            raise ValidationError({"username": "This field is required."})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError({"username": "User not found."})

        if not room.participants.filter(id=user.id).exists():
            return Response({"detail": "User not in room."}, status=status.HTTP_200_OK)

        # prevent removing the creator if you consider first participant the owner
        creator = room.participants.order_by("chatparticipant__joined_at").first()
        if user == creator:
            raise PermissionDenied("Cannot remove the room creator.")

        room.participants.remove(user)
        return Response({"detail": f"{username} removed."}, status=status.HTTP_200_OK)



class MessageViewSet(viewsets.ModelViewSet):
    """
    Requires ?room=<room_id> for list; creates message in a room the user belongs to.
    Sender is always the authenticated user (ignores provided 'sender').
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsRoomParticipant]

    def get_queryset(self):
        room_id = self.request.query_params.get("room")
        if not room_id:
            # No room specified -> show nothing (avoid leaking messages)
            return Message.objects.none()

        room = get_object_or_404(
            ChatRoom.objects.prefetch_related("participants"),
            pk=room_id
        )
        if not room.participants.filter(id=self.request.user.id).exists():
            # Not a participant -> no access
            return Message.objects.none()

        return (
            Message.objects
            .filter(chat_room=room)
            .select_related("chat_room", "sender")
            .order_by("timestamp")
        )

    def perform_create(self, serializer):
        room = serializer.validated_data.get("chat_room")
        if room is None:
            raise ValidationError({"chat_room": "This field is required."})

        if not room.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a participant of this room.")

        # Force sender to be the requester regardless of payload
        serializer.save(sender=self.request.user)



class ChatParticipantViewSet(viewsets.ModelViewSet):
    """
    Manage participation records. Lists participants of rooms the user belongs to.
    For create, requires 'user' == request.user and a room the user belongs to (join self to room).
    Also provides 'leave' action to deactivate/leave a room.
    """
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated, IsRoomParticipant]

    def get_queryset(self):
        room_id = self.request.query_params.get("room")
        qs = (
            ChatParticipant.objects
            .filter(chat_room__participants=self.request.user)
            .select_related("user", "chat_room")
            .order_by("-joined_at")
        )
        if room_id:
            qs = qs.filter(chat_room_id=room_id)
        return qs

    def perform_create(self, serializer):
        # Enforce that the 'user' in payload matches the requester
        payload_user = serializer.validated_data.get("user")
        room = serializer.validated_data.get("chat_room")

        if payload_user != self.request.user:
            raise PermissionDenied("You can only create participation for yourself.")

        if not room.participants.filter(id=self.request.user.id).exists():
            # Joining a room you don't belong to is allowed, but we must allow if user isn't yet a participant.
            # If you want invite-only rooms, flip this check to forbid unless invited.
            pass

        # Prevent duplicate membership
        if ChatParticipant.objects.filter(user=self.request.user, chat_room=room, is_active=True).exists():
            raise ValidationError("You are already an active participant of this room.")

        serializer.save()

    @action(detail=False, methods=["post"])
    def join(self, request):
        """
        Join a room by id: POST { "room": <id> }.
        """
        room_id = request.data.get("room")
        if not room_id:
            raise ValidationError({"room": "This field is required."})
        room = get_object_or_404(ChatRoom, pk=room_id)

        cp, created = ChatParticipant.objects.get_or_create(
            user=request.user, chat_room=room,
            defaults={"is_active": True}
        )
        if not created and not cp.is_active:
            cp.is_active = True
            cp.save(update_fields=["is_active"])
        elif not created:
            return Response({"detail": "Already a participant."}, status=status.HTTP_200_OK)

        room.participants.add(request.user)
        return Response({"detail": "Joined room."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def leave(self, request):
        """
        Leave a room by id: POST { "room": <id> }.
        Deactivates the participation and removes M2M link.
        """
        room_id = request.data.get("room")
        if not room_id:
            raise ValidationError({"room": "This field is required."})
        room = get_object_or_404(ChatRoom, pk=room_id)

        try:
            cp = ChatParticipant.objects.get(user=request.user, chat_room=room)
        except ChatParticipant.DoesNotExist:
            return Response({"detail": "Not a participant."}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: prevent creator from leaving
        creator = room.participants.order_by("chatparticipant__joined_at").first()
        if request.user == creator:
            raise PermissionDenied("Room creator cannot leave. Transfer ownership first.")

        cp.is_active = False
        cp.save(update_fields=["is_active"])
        room.participants.remove(request.user)
        return Response({"detail": "Left room."}, status=status.HTTP_200_OK)
