import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns  # noqa: E402
from chat.auth import JwtAuthMiddlewareStack    # noqa: E402
from chat.middleware import SimpleWsRateLimiter # noqa: E402



WS_MAX_EVENTS = int(os.environ.get("WS_MAX_EVENTS", "30"))
WS_PER_SECONDS = float(os.environ.get("WS_PER_SECONDS", "10"))

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": SimpleWsRateLimiter(
        JwtAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
        max_events=WS_MAX_EVENTS,
        per_seconds=WS_PER_SECONDS,
    ),
})
