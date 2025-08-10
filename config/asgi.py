import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_app = get_asgi_application()

# add chat.routing.websocket_urlpatterns in Phase 3
application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([])  # placeholder until chat app is added
    ),
})
