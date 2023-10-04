"""
Views for the user API.
"""
from rest_framework import (
    generics,
    authentication,
    permissions
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from .serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


class CreateUserApiView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class AuthTokenView(ObtainAuthToken):
    """Generate the custom authtoken using email instead of username."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserApiView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
