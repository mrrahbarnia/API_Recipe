"""
Tests for recipe API's.
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPE_LIST_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """Create and return a detail recipe URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return and upload image url by recipe's id."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe_with_new_tags(self):
        """Test for creating recipes with new tags."""
        payload = {
            'title': 'Thai prawn curry',
            'time_minutes': 20,
            'price': Decimal('8.50'),
            'link': 'http://example.com/recipe.pdf',
            'description': 'Sample description',
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }
        res = self.client.post(RECIPE_LIST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test for creating recipes with existing tags."""
        sample_tag = Tag.objects.create(user=self.user, name='Indian')

        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('5.60'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }
        res = self.client.post(RECIPE_LIST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(sample_tag, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_when_update_recipe(self):
        """Test for creating tags on updating recipes."""
        payload = {'tags': [{'name': 'breakfast'}]}

        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='breakfast')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        Breakfast_tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(Breakfast_tag)

        Lunch_tag = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(Lunch_tag, recipe.tags.all())
        self.assertNotIn(Breakfast_tag, recipe.tags.all())

    def test_clear_tags_when_update_recipe(self):
        """Test clearing recipe tags when updating a recipe."""
        Breakfast_tag = Tag.objects.create(user=self.user, name='Breakfast')
        Lunch_tag = Tag.objects.create(user=self.user, name='Lunch')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(Breakfast_tag)
        recipe.tags.add(Lunch_tag)

        payload = {'tags': []}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(Breakfast_tag, recipe.tags.all())
        self.assertNotIn(Lunch_tag, recipe.tags.all())
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test for creating recipe's with new ingredients successfully."""
        payload = {
            'title': 'Mast khiyar(Iranian food)',
            'time_minutes': 10,
            'price': Decimal('3.50'),
            'ingredients': [{'name': 'Yoghurt'}, {'name': 'Cocumber'}]
        }
        res = self.client.post(RECIPE_LIST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test for creating recipe's with existing
        ingredients withouth recreating them."""
        Ingredient.objects.create(user=self.user, name='Egg')
        payload = {
            'title': 'Omlet(Iranian food)',
            'time_minutes': 15,
            'price': Decimal('4.50'),
            'ingredients': [{'name': 'Egg'}, {'name': 'Tomato'}]
        }
        res = self.client.post(RECIPE_LIST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(ingredients.count(), 2)

    def test_create_ingredients_while_updating_recipe(self):
        """Test creating ingredients while updating a recipe successfully."""
        payload = {'ingredients': [{'name': 'Coconut'}]}
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 1)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Coconut')
        self.assertIn(new_ingredient, Ingredient.objects.all())

    def test_update_recipe_with_existing_ingredients(self):
        """Test assigning ingredients to recipe's with
        existing ingredients while updating recipe."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Lettuce')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Apple')
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        recipe.ingredients.add(ingredient1)

        payload = {'ingredients': [{'name': 'Apple'}]}
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clearing_ingredients_while_updating_recipe(self):
        """Test clearing ingredients while updating recipe's successfully."""
        ingredient = Ingredient.objects.create(user=self.user, name='Vanilla')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        url = recipe_detail_url(recipe.id)

        payload = {'ingredients': []}
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filtering_recipes_by_tags_successfully(self):
        """Test filtering recipes by their tags."""
        r1 = create_recipe(user=self.user, title='Recipe1')
        r2 = create_recipe(user=self.user, title='Recipe2')
        t1 = Tag.objects.create(user=self.user, name='Tag1')
        t2 = Tag.objects.create(user=self.user, name='Tag2')
        r1.tags.add(t1)
        r2.tags.add(t2)
        r3 = create_recipe(user=self.user, title='Recipe3')
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        paramas = {'tags': f'{t1.id},{t2.id}'}
        res = self.client.get(RECIPE_LIST_URL, paramas)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtering_recipes_by_their_ingredients(self):
        """Test filtering recipes by their ingredients."""
        r1 = create_recipe(user=self.user)
        r2 = create_recipe(user=self.user)
        r3 = create_recipe(user=self.user)
        i1 = Ingredient.objects.create(user=self.user, name='Ingredient1')
        i2 = Ingredient.objects.create(user=self.user, name='Ingredient2')
        r1.ingredients.add(i1)
        r2.ingredients.add(i2)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        params = {'ingredients': f'{i1.id},{i2.id}'}
        res = self.client.get(RECIPE_LIST_URL, params)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test uploading image API's."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='U123@example'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            """Creating a temporary file and save image in it for testing."""
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_with_invalid_data(self):
        """Test uploading image to a recipe with invalid data."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'baddata'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
