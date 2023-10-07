"""
Test for the ingredients API's.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_LIST_URL = reverse('recipe:ingredient-list')


def ingredient_detail_url(ingredient_id):
    """Return a detail url specific for each ingredient by it's id."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='U123@example'):
    """Create and return a user."""
    return get_user_model().objects.create_user(
        email=email, password=password
    )


class PublicIngredientApiTests(TestCase):
    """Tests for unauthenticated requests."""
    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        """Test for authentication required with response 401."""
        res = self.client.get(INGREDIENTS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Tests for authenticated user."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_list_of_ingredients_with_response_200(self):
        """Test for retrieving list of ingredients with authenticated user."""
        Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGREDIENTS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_list_of_ingredients_limited_to_user(self):
        """Test for retrieving a list of
        ingredients limited to authenticated user."""
        another_user = create_user(
            email='anotheruser@example.com',
            password='A123@example'
        )
        Ingredient.objects.create(user=another_user, name='Chocolate')
        ingredient = Ingredient.objects.create(user=self.user, name='Banana')

        res = self.client.get(INGREDIENTS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_updating_ingredient_successfully(self):
        """Test for updating ingredients with response 200."""
        ingredient = Ingredient.objects.create(user=self.user, name='Vanilla')
        payload = {'name': 'Rice'}
        url = ingredient_detail_url(ingredient.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredients_successfully(self):
        """Test for deleting ingredients with response 204."""
        ingredient = Ingredient.objects.create(user=self.user, name="Tomato")
        url = ingredient_detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())
