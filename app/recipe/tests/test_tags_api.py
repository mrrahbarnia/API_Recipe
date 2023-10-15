"""
Test for the tags API's.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Tag,
    Recipe
)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def tag_detail_url(tag_id):
    """Create and return the detail tag url."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='U123@example'):
    """Create and return a sample user."""
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTest(TestCase):
    """Test for unauthenticated requests."""
    def setUp(self):
        self.client = APIClient()

    def test_unathenticated_get_request_response_401(self):
        """Test for unauthenticated get request and recieve 401 error."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test for authenticated requests."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_list_of_tags(self):
        """Test retrieving a list of tags successfully."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_authenticated_user(self):
        """Test for showing tags that only belong to authenticated user."""
        another_user = create_user(email='anotheremail@example.com')
        sample_tag = Tag.objects.create(user=self.user, name='Fruity')
        Tag.objects.create(user=another_user, name='Spicy')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], sample_tag.name)
        self.assertEqual(res.data[0]['id'], sample_tag.id)

    def test_update_tag_successfully(self):
        """Test for updating tag API's."""
        sample_tag = Tag.objects.create(user=self.user, name='Comfort food')

        payload = {'name': 'Updated name'}
        res = self.client.patch(tag_detail_url(sample_tag.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sample_tag.refresh_from_db()
        self.assertEqual(sample_tag.name, payload['name'])

    def test_delete_tag_successfully(self):
        """Test for deleting tag API's."""
        sample_tag = Tag.objects.create(user=self.user, name='Breakfast')

        url = tag_detail_url(sample_tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(name='Breakfast').exists())

    def test_filter_tags_assigned_to_recipes_successfully(self):
        """Test listing tags to those assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name='Tag1')
        tag2 = Tag.objects.create(user=self.user, name='Tag2')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Sample recipe',
            description='Sample description',
            price=Decimal('5.50'),
            time_minutes=15
        )

        recipe1.tags.add(tag1)

        ser1 = TagSerializer(tag1)
        ser2 = TagSerializer(tag2)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertIn(ser1.data, res.data)
        self.assertNotIn(ser2.data, res.data)

    def test_filter_assigned_tags_unique(self):
        """Test filtered tags return a unique list."""
        tag1 = Tag.objects.create(user=self.user, name='Tag1')
        Tag.objects.create(user=self.user, name='Tag2')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Sample recipe',
            description='Sample description',
            price=Decimal('5.50'),
            time_minutes=15
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Sample recipe2',
            description='Sample description2',
            price=Decimal('5.50'),
            time_minutes=15
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
