"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


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