# core/channels_auth.py
import re

from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from rest_framework_simplejwt.authentication import JWTAuthentication



BEARER_RE = re.compile(r"^Bearer (?P<token>.+)$", re.I)

@database_sync_to_async
def _authenticate_token(token: str):
    auth = JWTAuthentication()
    try:
        validated = auth.get_validated_token(token)
        user = auth.get_user(validated)
        return user
    except Exception:
        return AnonymousUser()



class JwtAuthMiddleware:
    """
    Channels middleware that tries:
      1) Sec-WebSocket-Protocol/Authorization header with Bearer token
      2) `?token=<JWT>` in query string
    Falls back to AnonymousUser if no/invalid token.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Make sure DB connection is ready for auth call
        close_old_connections()

        headers = dict(scope.get("headers") or [])
        auth_header = None

        # Try 'authorization' header
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("latin1")

        token = None
        if auth_header:
            m = BEARER_RE.match(auth_header.strip())
            if m:
                token = m.group("token")

        # Try query string ?token=
        if not token:
            qs = parse_qs((scope.get("query_string") or b"").decode())
            token = (qs.get("token") or [None])[0]

        user = AnonymousUser()
        if token:
            user = await _authenticate_token(token) or AnonymousUser()

        scope["user"] = user
        return await self.inner(scope, receive, send)

def JwtAuthMiddlewareStack(inner):
    # Compose with default AuthMiddlewareStack so session/cookie auth still works
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
    
