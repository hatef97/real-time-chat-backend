import urllib.parse

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.db import close_old_connections

from rest_framework_simplejwt.authentication import JWTAuthentication



def _get_token_from_scope(scope):
    """
    Extract JWT from:
      - Authorization header: "Bearer <token>"
      - Query string: ?token=<token>
      - (optional) Sec-WebSocket-Protocol header (some clients use this)
    """
    # 1) Authorization header
    headers = dict(scope.get("headers") or [])
    auth_header = headers.get(b"authorization")
    if auth_header:
        try:
            prefix, raw = auth_header.decode().split(" ", 1)
            if prefix.lower() == "bearer":
                return raw.strip()
        except ValueError:
            pass

    # 2) Query string
    qs = scope.get("query_string", b"").decode()
    if qs:
        params = urllib.parse.parse_qs(qs)
        if "token" in params and params["token"]:
            return params["token"][0]

    # 3) Sec-WebSocket-Protocol
    swsp = headers.get(b"sec-websocket-protocol")
    if swsp:
        val = swsp.decode()
        # Some clients send just the token; others send comma-separated values
        parts = [p.strip() for p in val.split(",")]
        for p in parts:
            if p and p.lower() != "binary":
                return p

    return None


class JwtAuthMiddleware(BaseMiddleware):
    """
    Channels middleware that sets scope['user'] using SimpleJWT.
    Falls back to AnonymousUser if no/invalid token.
    """

    def __init__(self, inner):
        super().__init__(inner)
        self._auth = JWTAuthentication()
        self._User = get_user_model()

    async def __call__(self, scope, receive, send):
        close_old_connections()
        user = AnonymousUser()
        token = _get_token_from_scope(scope)

        if token:
            user = await self._authenticate(token)

        scope["user"] = user
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _authenticate(self, raw_token):
        try:
            validated = self._auth.get_validated_token(raw_token)
            return self._auth.get_user(validated)
        except Exception:
            return AnonymousUser()


def JwtAuthMiddlewareStack(inner):
    """
    Keep default channel auth (cookies/session) AND accept JWTs.
    """
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
