"""
Tests for recipe API's.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPE_LIST_URL = reverse('recipe:recipe-list')


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'sample title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRescipeApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPE_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'U123@example'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_LIST_URL)

        recipe_list = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipe_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        another_user = get_user_model().objects.create_user(
            'anotheruser@example.com',
            'T123@example'
        )
        create_recipe(user=another_user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_LIST_URL)

        recipe_list = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
