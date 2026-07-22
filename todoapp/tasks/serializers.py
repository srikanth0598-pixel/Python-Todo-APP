from rest_framework import serializers
from .models import Category, Todo, User, Tag, ActivityLog, Notification, Comment, Attachment
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

    def validate_username(self, value):
        if AuthUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if AuthUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        return AuthUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )


class AuthUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = "__all__"
        read_only_fields = ("id", "user")


class AttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class CommentSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = (
            "id",
            "user",
            "created_at",
            "user_name"
        )
class TodoListSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()

    class Meta:
        model = Todo
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "is_pinned",
            "category",
        )
class TodoDetailSerializer(serializers.ModelSerializer):

    category = CategorySerializer(read_only=True)

    attachments = AttachmentSerializer(
        many=True,
        read_only=True
    )

    comments = CommentSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Todo
        fields = "__all__"



class TodoCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Todo
        exclude = (
            "user",
            "created_at",
            "updated_at",
            "is_deleted",
        )

    def validate_title(self, value):

        if len(value) < 3:
            raise serializers.ValidationError(
                "Title must contain at least 3 characters."
            )

        return value

    def validate(self, attrs):

        if (
            attrs.get("status") == "completed"
            and not attrs.get("due_date")
        ):
            pass

        return attrs

class TodoUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Todo
        exclude = (
            "user",
            "created_at",
            "updated_at",
        )
class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
        )
class ActivitySerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    todo = serializers.StringRelatedField()

    class Meta:
        model = ActivityLog
        fields = "__all__"