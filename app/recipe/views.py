"""
Views for recipe API's.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma seprated list of tag IDs to filter.'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma seprated list of ingredient IDs to filter.'
            )
        ]
    )
)
class RecipeApiViewSet(viewsets.ModelViewSet):
    """View for manage recipe API's."""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def _params_to_ints(self, qs):
        """Convert a list of string parameters to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Get recipes which only belong to authenticated user."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(
            user=self.request.user).order_by('-id').distinct()

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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.'
            ),
        ]
    )
)
class BaseRecipeAttrApiViewSet(mixins.DestroyModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    """Base class for recipe attributes."""
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tags that belong to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(
            user=self.request.user).order_by('-name').distinct()


class TagApiViewSet(BaseRecipeAttrApiViewSet):
    """View for managing tags API's."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientApiViewSet(BaseRecipeAttrApiViewSet):
    """View for managing ingredients API's."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
