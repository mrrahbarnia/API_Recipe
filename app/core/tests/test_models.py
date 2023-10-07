"""
Tests for models.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='Test@email.com', password='T123@example'):
    """Helper function for creating users."""
    return get_user_model().objects.create_user(email, password)


class TestModels(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test for creating a user with an email successfully"""
        email = "test@examle.com"
        password = "T123@example"
        user = get_user_model().objects.create_user(
            email=email, password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['test2@example.COM', 'test2@example.com'],
            ['Test3@example.com', 'Test3@example.com'],
            ['TEST4@EXAMPLE.COM', 'TEST4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email, password='T123@example'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_rases_error(self):
        """Test that creating a user without an email raises ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'T123@example')

    def test_create_super_user(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'T123@example'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test for creating recipe successfully."""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='T123@example'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="test",
            time_minutes=5,
            price=Decimal('5.50'),
            description="test-description"
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_instance_in_tag_model(self):
        """Test for tag model to check
        whether it works successfully or not."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertTrue(models.Tag.objects.filter(name='Tag1').exists())
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredients_successfully(self):
        """Test for creating an instance of ingredient model."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient1'
        )

        self.assertEqual(str(ingredient), ingredient.name)
        self.assertTrue(models.Ingredient.objects.filter(
            name='Ingredient1').exists()
        )
