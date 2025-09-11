import pytest

from chat.models import ChatRoom, Message
from core.models import User



@pytest.mark.django_db
def test_make_message():
    u = User.objects.create_user(username="bob")
    room = ChatRoom.objects.create(name="lobby")

    msg = Message.objects.create(chat_room=room, sender=u, content="hi")

    assert msg.chat_room_id == room.id
    assert msg.sender_id == u.id
    assert msg.content == "hi"  
    
