import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from users.serializers import RegisterSerializer

@pytest.mark.django_db
class TestUsersSerializers(TestCase):

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "password": "strongpassword123"
        }

    def test_register_serializer_valid(self):
        """Test walidacji poprawnego serializatora rejestracji"""
        serializer = RegisterSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_register_serializer_duplicate_username(self):
        """Test blokady rejestracji istniejącego użytkownika"""
        User.objects.create_user(**self.user_data)
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)