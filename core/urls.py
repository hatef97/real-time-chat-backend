from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, UserMeViewSet



# Create a router and register the viewsets
router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'me', UserMeViewSet, basename='user-me')



urlpatterns = router.urls
