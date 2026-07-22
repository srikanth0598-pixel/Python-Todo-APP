from rest_framework import serializers
from .models import Todo, User
from django.contrib.auth import get_user_model

AuthUser = get_user_model()

class TodoSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=100)
    completed = serializers.BooleanField(default=False)

    class Meta:
        model = Todo
        fields = ['id', 'title', 'completed']
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=100)
    google_id = serializers.CharField(max_length=100)
    picture = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'google_id', 'picture']

class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        # expose common fields; adapt if your AUTH_USER_MODEL differs
        fields = ["id", "username", "email", "first_name", "last_name"]


class AuthUserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        return AuthUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )