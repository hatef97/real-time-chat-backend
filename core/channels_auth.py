import re
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from core.models import User

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import close_old_connections

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings as sj_settings  # ✅



BEARER_RE = re.compile(r"^Bearer (?P<token>.+)$", re.I)



# ✅ cached, DB-hit-minimizing user resolver
@database_sync_to_async
def _user_from_validated_token_cached(validated_token):
    """
    Resolve user from SimpleJWT validated token with a tiny cache.
    Caches the User instance for 60s to avoid repeated DB hits on reconnects.
    """
    # respect custom USER_ID_CLAIM if you changed it in SIMPLE_JWT
    user_id_claim = getattr(sj_settings, "USER_ID_CLAIM", "user_id")
    user_id = validated_token.get(user_id_claim)
    if not user_id:
        return None

    key = f"user:{user_id}"
    user = cache.get(key)
    if user is not None:
        return user

    try:
        # keep it lightweight; only what you need for auth
        user = User.objects.only("id", "is_active").get(pk=user_id, is_active=True)
        cache.set(key, user, 60)  # tiny TTL; safe if user deactivations are rare
        return user
    except User.DoesNotExist:
        return None



@database_sync_to_async
def _validate_token(token: str):
    auth = JWTAuthentication()
    # Just validate & return the validated token; we do user fetch ourselves (cached)
    return auth.get_validated_token(token)



class JwtAuthMiddleware:
    """
    Tries:
      1) Authorization: Bearer <JWT>
      2) ?token=<JWT>
    Falls back to AnonymousUser on missing/invalid token.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()

        headers = dict(scope.get("headers") or [])
        auth_header = headers.get(b"authorization")
        token = None

        if auth_header:
            m = BEARER_RE.match(auth_header.decode("latin1").strip())
            if m:
                token = m.group("token")

        if not token:
            qs = parse_qs((scope.get("query_string") or b"").decode())
            token = (qs.get("token") or [None])[0]

        user = AnonymousUser()
        if token:
            try:
                # ✅ validate once…
                validated = await _validate_token(token)
                # ✅ …then resolve user via cache-aware lookup
                user = await _user_from_validated_token_cached(validated) or AnonymousUser()
            except Exception:
                user = AnonymousUser()

        scope["user"] = user
        return await self.inner(scope, receive, send)



def JwtAuthMiddlewareStack(inner):
    # Keep session/cookie auth compatibility
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))

