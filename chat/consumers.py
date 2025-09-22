import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth.models import AnonymousUser

from .models import ChatRoom, ChatParticipant, Message, Presence



logger = logging.getLogger(__name__)

def room_group_name(room_id: int) -> str:
    return f"room_{room_id}"


@sync_to_async
def user_is_participant(room_id: int, user_id: int) -> bool:
    return ChatParticipant.objects.filter(chat_room_id=room_id, user_id=user_id).exists()


@sync_to_async
def create_message(room_id: int, user_id: int, content: str) -> dict:
    msg = Message.objects.create(chat_room_id=room_id, sender_id=user_id, content=content)
    return {
        "id": msg.id,
        "room_id": room_id,
        "sender_id": user_id,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() if hasattr(msg, "created_at") else None,
    }


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.rooms = set()
        self.room_group_name = None
        self.room_id = self.scope.get("url_route", {}).get("kwargs", {}).get("room_id")
        self.user = self.scope.get("user")

        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4401)  # Unauthorized
            return

        await self.accept()
        await self._presence_up()

    async def disconnect(self, code):
        if code == 4408:
            logger.warning(
                "WebSocket 4408 (policy violation / throttled) user=%s",
                getattr(self.scope.get("user"), "id", None),
            )

        if getattr(self, "rooms", None):
            for gid in list(self.rooms):
                await self.channel_layer.group_discard(gid, self.channel_name)
                self.rooms.discard(gid)

        await self._presence_down()

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "join":
            await self._join(content)
        elif action == "leave":
            await self._leave(content)
        elif action == "send_message":
            await self._send_message(content)
        elif action == "typing":
            await self._typing(content)
        else:
            await self.send_json({"type": "error", "detail": "unknown_action"})

    async def _join(self, payload):
        room_id = payload.get("room_id")
        if not isinstance(room_id, int):
            return await self.send_json({"type": "error", "detail": "room_id_required"})
        user = self.scope["user"]
        if not await user_is_participant(room_id, user.id):
            return await self.send_json({"type": "error", "detail": "not_a_participant"})

        gid = room_group_name(room_id)
        await self.channel_layer.group_add(gid, self.channel_name)
        self.rooms.add(gid)
        await self.send_json({"type": "joined", "room_id": room_id})

    async def _leave(self, payload):
        room_id = payload.get("room_id")
        gid = room_group_name(room_id)
        if gid in self.rooms:
            await self.channel_layer.group_discard(gid, self.channel_name)
            self.rooms.discard(gid)
        await self.send_json({"type": "left", "room_id": room_id})

    async def _send_message(self, payload):
        room_id = payload.get("room_id")
        content = (payload.get("content") or "").strip()
        temp_id = payload.get("temp_id")
        if not content:
            return await self.send_json({"type": "error", "detail": "empty_content"})
        user = self.scope["user"]
        if not await user_is_participant(room_id, user.id):
            return await self.send_json({"type": "error", "detail": "not_a_participant"})

        message = await create_message(room_id, user.id, content)

        # ACK creator (bind temp_id for optimistic UI)
        await self.send_json({"type": "message_created", "message": message, "temp_id": temp_id})

        # Broadcast to everyone in the room
        await self.channel_layer.group_send(
            room_group_name(room_id),
            {"type": "broadcast.message", "message": message, "sender_id": user.id},
        )

    async def _typing(self, payload):
        room_id = payload.get("room_id")
        is_typing = bool(payload.get("is_typing"))
        user = self.scope["user"]
        if not await user_is_participant(room_id, user.id):
            return
        await self.channel_layer.group_send(
            room_group_name(room_id),
            {"type": "broadcast.typing", "room_id": room_id, "user_id": user.id, "is_typing": is_typing},
        )

    # Presence management
    @database_sync_to_async
    def _presence_up(self):
        if self.user and self.user.is_authenticated:
            Presence.objects.update_or_create(
                user_id=self.user.id,
                channel_name=self.channel_name,
                defaults={"room_id": self.room_id},
            )

    @database_sync_to_async
    def _presence_down(self):
        Presence.objects.filter(channel_name=self.channel_name).delete()

    # Group event handlers
    async def broadcast_message(self, event):
        await self.send_json({"type": "message_created", "message": event["message"]})

    async def broadcast_typing(self, event):
        await self.send_json({"type": "typing", **{k: event[k] for k in ("room_id", "user_id", "is_typing")}})

