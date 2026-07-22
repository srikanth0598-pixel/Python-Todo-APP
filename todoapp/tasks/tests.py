from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from tasks.views import create_user_tokens


class AuthUserRegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_uses_name_for_username_and_defaults_password(self):
        response = self.client.post(
            reverse("auth-user-register"),
            {"name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "Jane Doe")

        user = get_user_model().objects.get(username="Jane Doe")
        self.assertTrue(user.check_password("admin@123"))

    def test_register_returns_error_for_existing_username(self):
        get_user_model().objects.create_user(username="existing", email="first@example.com", password="password123")

        response = self.client.post(
            reverse("auth-user-register"),
            {"username": "existing", "email": "second@example.com", "password": "password123"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("A user with that username already exists.", response.json()["username"])

    def test_register_returns_error_for_invalid_email(self):
        response = self.client.post(
            reverse("auth-user-register"),
            {"username": "newuser", "email": "not-an-email", "password": "password123"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Enter a valid email address.", response.json()["email"])

    def test_register_sends_welcome_email(self):
        with patch("tasks.views.send_mail") as mock_send_mail:
            response = self.client.post(
                reverse("auth-user-register"),
                {"username": "welcomeuser", "email": "welcome@example.com", "password": "password123"},
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        mock_send_mail.assert_called_once()


class GoogleCallbackTests(TestCase):
    def test_google_callback_creates_django_auth_user(self):
        with patch("tasks.views.requests.post") as mock_post, patch("tasks.views.requests.get") as mock_get:
            mock_post.return_value.json.return_value = {"access_token": "test-token"}
            mock_get.return_value.json.return_value = {
                "email": "googleuser@example.com",
                "name": "Google User",
                "id": "google-123",
                "picture": "https://example.com/avatar.png",
            }

            response = self.client.get(reverse("google-callback"), {"code": "test-code"})

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email="googleuser@example.com")
        self.assertEqual(user.username, "Google User")
        self.assertTrue(user.check_password("admin1234"))


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="tokenuser",
            email="tokenuser@example.com",
            password="password123",
        )

    def test_create_user_tokens_returns_jwt_tokens(self):
        tokens = create_user_tokens(self.user)

        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertIsInstance(AccessToken(tokens["access_token"]), AccessToken)
        self.assertIsInstance(RefreshToken(tokens["refresh_token"]), RefreshToken)

    def test_refresh_token_returns_new_access_token(self):
        tokens = create_user_tokens(self.user)

        response = self.client.post(
            reverse("auth-user-refresh"),
            {"refresh_token": tokens["refresh_token"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertIn("refresh_token", response.json())


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile_returns_user_details(self):
        response = self.client.get(reverse("profile-detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "profileuser")

    def test_get_profile_with_bearer_token(self):
        tokens = create_user_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")

        response = self.client.get(reverse("profile-detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "profileuser")

    def test_update_profile_updates_user_details(self):
        response = self.client.patch(
            reverse("profile-detail"),
            {"first_name": "Updated", "last_name": "User"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "User")
