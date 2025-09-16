import os
from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application

from chat.routing import websocket_urlpatterns
from chat.auth import JwtAuthMiddlewareStack
from chat.middleware import SimpleWsRateLimiter



django_asgi_app = get_asgi_application()

# Optional: make limits env-driven
WS_MAX_EVENTS = int(os.environ.get("WS_MAX_EVENTS", "30"))     # events per window
WS_PER_SECONDS = float(os.environ.get("WS_PER_SECONDS", "10")) # window size (s)

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
