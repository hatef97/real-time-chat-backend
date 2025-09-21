from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from djoser.views import UserViewSet



urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Djoser (users & auth)
    path("auth/", include("djoser.urls")),  # user endpoints
    path("auth/", include("djoser.urls.jwt")),  # /jwt/create, /jwt/refresh, etc.
    
    # Core app
    path('api/core/', include('core.urls')),
    
    # chat app
    path('api/chat/', include(("chat.urls", "chat"), namespace="chat")),

    # healthz
    path("healthz/", include("health_check.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
