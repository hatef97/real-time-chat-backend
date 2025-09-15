import pytest

from django.urls import reverse

from rest_framework.test import APIClient

from chat.models import ChatRoom, ChatParticipant
from core.models import User



@pytest.mark.django_db
def test_message_list_cache_busts_on_create():
    u = User.objects.create_user(username="u", password="x")
    room = ChatRoom.objects.create(name="lobby")
    ChatParticipant.objects.create(chat_room=room, user=u)
    client = APIClient()
    client.force_authenticate(user=u)

    list_url = reverse("chat:message-list", kwargs={"room_id": room.id})

    # Prime cache
    r1 = client.get(list_url, {"page_size": 100})
    assert r1.status_code == 200
    before_contents = [m["content"] for m in r1.data]

    # Create new message
    r_create = client.post(list_url, {"content": "cache-test-123"}, format="json")
    assert r_create.status_code in (200, 201)

    # Same params → should reflect bumped version
    r2 = client.get(list_url, {"page_size": 100})
    assert r2.status_code == 200
    after_contents = [m["content"] for m in r2.data]
    assert "cache-test-123" in after_contents
    # and previous messages are preserved
    for c in before_contents:
        assert c in after_contents
