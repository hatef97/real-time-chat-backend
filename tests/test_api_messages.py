import pytest

from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from core.models import User
from chat.models import ChatRoom, ChatParticipant, Message



@pytest.mark.django_db
def test_list_and_create_messages_via_api():
    # Arrange: user, room, membership
    u = User.objects.create_user(username="apiuser", password="x")
    room = ChatRoom.objects.create(name="lobby")
    ChatParticipant.objects.create(chat_room=room, user=u)

    client = APIClient()
    client.force_authenticate(user=u)

    # --- Choose ONE of these reverse() patterns, depending on your urls.py ---

    # Pattern A: nested messages under room
    #   path("api/rooms/<int:room_id>/messages/", ...)
    try:
        list_url = reverse("chat:message-list", kwargs={"room_id": room.id})
    except Exception:
        # Pattern B: explicit route name
        #   path("api/chats/<int:room_id>/messages/", ...)
        list_url = reverse("chat:room-messages", kwargs={"room_id": room.id})

    # List should be 200 OK and start empty
    r = client.get(list_url)
    assert r.status_code == 200
    assert isinstance(r.data, list)
    assert len(r.data) == 0

    # Create a message (POST)
    payload = {"content": "hello from API"}
    r = client.post(list_url, payload, format="json")
    assert r.status_code in (200, 201)
    assert r.data.get("content") == "hello from API"

    # List again -> should contain 1 message
    r = client.get(list_url)
    assert r.status_code == 200
    assert any(m.get("content") == "hello from API" for m in r.data)

    # DB sanity
    assert Message.objects.filter(chat_room=room, sender=u, content="hello from API").exists()

