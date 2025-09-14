import pytest

from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from core.models import User
from chat.models import ChatRoom, ChatParticipant



@pytest.mark.django_db
def test_message_list_cache_busts_on_create():
    u = User.objects.create_user(username="u", password="x")
    room = ChatRoom.objects.create(name="lobby")
    ChatParticipant.objects.create(chat_room=room, user=u)
    client = APIClient()
    client.force_authenticate(user=u)

    list_url = reverse("chat:message-list", kwargs={"room_id": room.id})

    # Baseline (whatever page policy is)
    r1 = client.get(list_url, {"page_size": 100})
    assert r1.status_code == 200
    before_contents = [m["content"] for m in r1.data]

    # Create a new message
    create_payload = {"content": "cache-test-123"}
    r_create = client.post(list_url, create_payload, format="json")
    assert r_create.status_code in (200, 201)

    # Fetch again → should reflect the new message (cache version bumped)
    r2 = client.get(list_url, {"page_size": 100})
    assert r2.status_code == 200
    after_contents = [m["content"] for m in r2.data]

    # Must include the new message
    assert "cache-test-123" in after_contents

    # And the response should differ from the baseline (cache actually invalidated)
    assert after_contents != before_contents
