import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from config.asgi import application
from core.models import User

from rest_framework_simplejwt.tokens import RefreshToken



@pytest.mark.asyncio
@pytest.mark.django_db
async def test_ws_reject_without_token():
    comm = WebsocketCommunicator(application, "/ws/chat/")
    connected, _ = await comm.connect()
    assert connected is False
    if connected:
        await comm.disconnect()


@database_sync_to_async
def _create_user(username="alice", password="x"):
    return User.objects.create_user(username=username, password=password)

@database_sync_to_async
def _access_for(user):
    return str(RefreshToken.for_user(user).access_token)


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_ws_accept_with_token():
    user = await _create_user()
    token = await _access_for(user)

    comm = WebsocketCommunicator(
        application, "/ws/chat/",
        headers=[(b"authorization", f"Bearer {token}".encode())]
    )
    connected, _ = await comm.connect()
    assert connected is True
    await comm.disconnect()
