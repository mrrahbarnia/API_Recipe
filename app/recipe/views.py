"""
Views for recipe API's.
"""
from rest_framework.response import Response
from rest_framework import (
    viewsets,
    mixins,
    status
)
from rest_framework import (
    authentication,
    permissions
)
from rest_framework.decorators import action

from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeImageSerializer
)

from core.models import (
    Recipe,
    Tag,
    Ingredient
)


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
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Defining a method called upload_image
        for uploading images for recipe's"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrApiViewSet(mixins.DestroyModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    """Base class for recipe attributes."""
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tags that belong to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagApiViewSet(BaseRecipeAttrApiViewSet):
    """View for managing tags API's."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientApiViewSet(BaseRecipeAttrApiViewSet):
    """View for managing ingredients API's."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
