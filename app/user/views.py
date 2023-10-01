"""
Views for the user API.
"""
from rest_framework import generics

from .serializers import UserSerializer


class CreateUserApiView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer
