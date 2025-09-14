from django.core.cache import cache



# Base key spaces
ROOM_VERSION_KEY = "chat:room:{room_id}:v"              # int version per room
ROOM_MESSAGES_KEY = "chat:room:{room_id}:messages:v{v}" # serialized list

# TTLs
ROOM_MESSAGES_TTL = 300  # seconds; tune as needed

def _room_version_key(room_id: int) -> str:
    return ROOM_VERSION_KEY.format(room_id=room_id)

def get_room_version(room_id: int) -> int:
    """
    Get current version for a room; initialize to 1 if absent.
    """
    v = cache.get(_room_version_key(room_id))
    if v is None:
        v = 1
        cache.set(_room_version_key(room_id), v, None)
    return int(v)

def bump_room_version(room_id: int) -> int:
    """
    Atomically bump version so old list keys are bypassed.
    """
    key = _room_version_key(room_id)
    try:
        # Works with django-redis (atomic)
        v = cache.incr(key)
    except Exception:
        # Fallback: set if missing, else get+set
        v = cache.get(key)
        if v is None:
            v = 1
        v = int(v) + 1
        cache.set(key, v, None)
    return v

def room_messages_cache_key(room_id: int, version: int) -> str:
    return ROOM_MESSAGES_KEY.format(room_id=room_id, v=version)

def get_room_messages_cached(room_id: int):
    v = get_room_version(room_id)
    key = room_messages_cache_key(room_id, v)
    return cache.get(key), key, v

def set_room_messages_cache(key: str, data):
    cache.set(key, data, ROOM_MESSAGES_TTL)
