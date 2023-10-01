"""
Views for the user API.
"""
from rest_framework import generics
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
    