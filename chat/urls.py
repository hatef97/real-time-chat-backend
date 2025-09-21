from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet, MessageViewSet, ChatParticipantViewSet, RoomOnlineView



app_name = "chat"



router = DefaultRouter()
router.register(r'chat-rooms', ChatRoomViewSet, basename='chat-room')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'participants', ChatParticipantViewSet, basename='chat-participant')



urlpatterns = [
    # existing router endpoints
    path("", include(router.urls)),

    # reverse("chat:message-list", kwargs={"room_id": <id>})
    path(
        "api/rooms/<int:room_id>/messages/",
        MessageViewSet.as_view({"get": "list", "post": "create"}),
        name="message-list",
    ),
    path("rooms/<int:room_id>/online/", RoomOnlineView.as_view(), name="room-online"),
]
