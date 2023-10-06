"""
Views for recipe API's.
"""
from rest_framework import viewsets, mixins
from rest_framework import (
    authentication,
    permissions
)
from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer
)

from core.models import Recipe, Tag


class RecipeApiViewSet(viewsets.ModelViewSet):
    """View for manage recipe API's."""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get_queryset(self):
        """Get recipes which only belong to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """This function defines that when the base class uses
        RecipeSerializer and when uses RecipeDetailSerializer."""
        if self.action == 'list':
            return RecipeSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)


class TagApiViewSet(mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """View for manage tags API's."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tags that belong to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')
