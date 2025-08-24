from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet, MessageViewSet, ChatParticipantViewSet



router = DefaultRouter()
router.register(r'chat-rooms', ChatRoomViewSet, basename='chat-room')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'participants', ChatParticipantViewSet, basename='chat-participant')



urlpatterns = router.urls
