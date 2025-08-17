from django.contrib import admin
from django.urls import path, include

from djoser.views import UserViewSet



urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Djoser (users & auth)
    path("auth/", include("djoser.urls")),  # user endpoints
    path("auth/", include("djoser.urls.jwt")),  # /jwt/create, /jwt/refresh, etc.
    
    # Core app
    path('api/core/', include('core.urls')),
]
