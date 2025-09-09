# config/settings_test.py
from .settings import *  # import your base settings



# Use SQLite for tests (no external DB needed)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # or ":memory:" for pure in-memory
    }
}

# Fast hashing for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory channel layer (no Redis needed)
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}

# Local memory cache (avoid Redis in tests)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique",
    }
}

# Email to memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Make sure DEBUG doesn’t interfere with static handler during tests
DEBUG = False
