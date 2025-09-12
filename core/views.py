from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User, Profile
from .serializers import ProfileSerializer, UserMeSerializer



class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user profiles.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally restricts the returned profiles to the user’s profile,
        by filtering against the authenticated user.
        """
        return self.queryset.filter(user=self.request.user)



class UserMeViewSet(viewsets.ModelViewSet):
    """
    A viewset for the /me endpoint, allowing users to view and update their information.
    """
    queryset = User.objects.all()
    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        This will ensure we always access the authenticated user.
        """
        return self.request.user

    def perform_update(self, serializer):
        """
        Handle the saving of the user and profile when updating.
        """
        user = self.get_object()
        serializer.save(user=user)
        super().perform_update(serializer)

