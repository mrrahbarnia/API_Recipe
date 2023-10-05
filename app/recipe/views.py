"""
Views for recipe API's.
"""
from rest_framework import viewsets
from rest_framework import (
    authentication,
    permissions
)
from .serializers import RecipeSerializer

from core.models import Recipe


class RecipeApiViewSet(viewsets.ModelViewSet):
    """View for manage recipe API's."""
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get_queryset(self):
        """Get recipes which only belong to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')
