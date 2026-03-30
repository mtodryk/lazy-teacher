import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

@pytest.mark.django_db
class TestUsersAPIs(APITestCase):

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "password": "strongpassword123"
        }
        self.register_url = reverse("users-register")
        self.login_url = reverse("users-login")
        self.logout_url = reverse("users-logout")

    def test_api_register_user(self):
        """Test tworzenia użytkownika przez API"""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], self.user_data["username"])

    def test_api_login_user(self):
        """Test logowania i otrzymywania tokena"""
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_api_login_invalid_credentials(self):
        """Test logowania błędnymi danymi"""
        User.objects.create_user(**self.user_data)
        wrong_data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.login_url, wrong_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_logout_authenticated(self):
        """Test wylogowania zalogowanego użytkownika"""
        user = User.objects.create_user(**self.user_data)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_api_logout_unauthenticated(self):
        """Test wylogowania bez tokena"""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)