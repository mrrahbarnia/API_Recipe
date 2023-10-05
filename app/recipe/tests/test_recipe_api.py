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

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPE_LIST_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """Create and return a detail recipe URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


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


def create_user(**params):
    """Creating user as a hepler function to write less codes."""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(
            email='user@example.com',
            password='U123@example'
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
        another_user = create_user(
            email='anotheruser@example.com',
            password='T123@example'
        )
        create_recipe(user=another_user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_LIST_URL)

        recipe_list = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_detail_recipe_url(self):
        """Test for retrieving the detail recipe url."""
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_successfully(self):
        """Test for creating recipe."""
        payload = {
            'title': 'Sample title',
            'time_minutes': 35,
            'price': Decimal('10.25')
        }
        res = self.client.post(RECIPE_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipes(self):
        """Test for partial updating works successfully."""
        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample title',
            link=original_link
        )
        url = recipe_detail_url(recipe.id)
        payload = {'title': 'New title'}
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, original_link)

    def test_full_update_recipes(self):
        """Test for full update/PUT method works successfully."""
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        payload = {
            'title': 'New title',
            'time_minutes': 15,
            'price': Decimal('7.50'),
            'description': 'New description',
            'link': 'http://example.com/new-link'
        }
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_attribute_raises_error(self):
        """Test for changing user attribute of a recipe."""
        another_user = create_user(
            email='anotheruser@example.com', password='A123@example'
        )
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        payload = {'user': another_user.id}
        self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe_successfully(self):
        """Test for deleting a recipe with 204 NO CONTENT."""
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_another_user_recipes_response_404(self):
        """Test to trying delete recipes that belong to another user."""
        another_user = create_user(
            email='anotheruser@example.com',
            password='A123@example'
        )
        recipe = create_recipe(user=another_user)
        url = recipe_detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
