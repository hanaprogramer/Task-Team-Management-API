from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from apps.users.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer
)

User = get_user_model()


class UserSerializerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="hana",
            email="hana@test.com",
            password="1234StrongPass!"
        )

    # ==================================================
    # UserSerializer
    # ==================================================
    def test_user_serializer_fields(self):
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("username", data)
        self.assertIn("email", data)
        self.assertIn("role", data)
        self.assertIn("is_active", data)

    # ==================================================
    # RegisterSerializer
    # ==================================================
    def test_register_serializer_success(self):
        payload = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "1234StrongPass!"
        }

        serializer = RegisterSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@test.com")
        self.assertEqual(user.role, "member")   # role همیشه member
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("1234StrongPass!"))

    def test_register_serializer_password_validation_fail(self):
        payload = {
            "username": "weakuser",
            "email": "weak@test.com",
            "password": "123"   # خیلی ضعیف
        }
        serializer = RegisterSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    # ==================================================
    # LoginSerializer
    # ==================================================
    def test_login_serializer_success(self):
        payload = {
            "username": "hana",
            "password": "1234StrongPass!"
        }
        serializer = LoginSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_login_serializer_fail_wrong_password(self):
        payload = {
            "username": "hana",
            "password": "wrongpass"
        }
        serializer = LoginSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_login_serializer_fail_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        payload = {
            "username": "hana",
            "password": "1234StrongPass!"
        }
        serializer = LoginSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    # ==================================================
    # LogoutSerializer
    # ==================================================
    def test_logout_serializer_success(self):
        payload = {"refresh": "some-refresh-token"}
        serializer = LogoutSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_logout_serializer_fail_no_refresh(self):
        payload = {}
        serializer = LogoutSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)
