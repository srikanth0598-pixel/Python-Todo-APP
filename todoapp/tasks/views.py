# pyrefly: ignore [missing-import]
from datetime import timedelta
import logging
import secrets
from urllib.parse import urlencode
from django.conf import settings
from  django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.views import APIView

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Todo, User,Category
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from .serializers import (
    TodoSerializer,
    UserSerializer,
    ExcelUploadSerializer,
    AuthUserSerializer,
    AuthUserRegisterSerializer,
    AuthUserProfileSerializer,
    CategorySerializer
)
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
import os
import pandas as pd
from rest_framework import status
import requests
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from dotenv import load_dotenv
load_dotenv()
# Create your views here.

logger = logging.getLogger(__name__)

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

from .serializers import (
    TodoCreateSerializer,
    TodoUpdateSerializer,
    TodoListSerializer,
    TodoDetailSerializer
)


class TodoCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = TodoCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
@authentication_classes([JWTAuthentication])   # 👈 Force JWT only
@permission_classes([IsAuthenticated])
class TodoListAPIView(APIView):
    

    def get(self, request):

        todos = Todo.objects.filter(
            user=request.user,
            is_deleted=False
        )

        serializer = TodoListSerializer(
            todos,
            many=True
        )

        return Response(serializer.data)
class TodoDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        try:

            todo = Todo.objects.get(
                id=pk,
                user=request.user
            )

        except Todo.DoesNotExist:

            return Response(
                {"message": "Todo not found"},
                status=404
            )

        serializer = TodoDetailSerializer(todo)

        return Response(serializer.data)
class TodoUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):

        try:

            todo = Todo.objects.get(
                id=pk,
                user=request.user
            )

        except Todo.DoesNotExist:

            return Response(
                {"message": "Todo not found"},
                status=404
            )

        serializer = TodoUpdateSerializer(
            todo,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)

class TodoDeleteAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        try:

            todo = Todo.objects.get(
                id=pk,
                user=request.user
            )

        except Todo.DoesNotExist:

            return Response(
                {"message": "Todo not found"},
                status=404
            )

        todo.is_deleted = True

        todo.save()

        return Response(
            {"message": "Todo deleted successfully"}
        )
class TodoStatusAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        try:

            todo = Todo.objects.get(
                id=pk,
                user=request.user
            )

        except Todo.DoesNotExist:

            return Response(
                {"message": "Todo not found"},
                status=404
            )

        todo.status = request.data.get(
            "status",
            todo.status
        )

        todo.save()

        return Response(
            {"message": "Status updated"}
        )
class TodoPinAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        todo = Todo.objects.get(
            id=pk,
            user=request.user
        )

        todo.is_pinned = not todo.is_pinned

        todo.save()

        return Response(
            {"is_pinned": todo.is_pinned}
        )
from django.db.models import Q


class TodoSearchAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        keyword = request.GET.get("search")

        todos = Todo.objects.filter(
            Q(title__icontains=keyword) |
            Q(description__icontains=keyword),
            user=request.user,
            is_deleted=False
        )

        serializer = TodoListSerializer(
            todos,
            many=True
        )

        return Response(serializer.data)
class CategoryCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CategorySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(
            user=request.user
        )

        return Response(serializer.data)
class CategoryListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        categories = Category.objects.filter(
            user=request.user
        )

        serializer = CategorySerializer(
            categories,
            many=True
        )

        return Response(serializer.data)
def create_user_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


def decode_token(token, salt=None):
    auth = JWTAuthentication()
    validated_token = auth.get_validated_token(token)
    payload = validated_token.payload
    return {
        "token_type": payload.get("token_type", "access"),
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "google_id": payload.get("google_id"),
    }


def redirect_to_frontend(user, message):
    serializer = UserSerializer(user)
    tokens = create_user_tokens(user)
    query_params = {
        "message": message,
        "user_id": serializer.data["id"],
        "email": serializer.data["email"],
        "name": serializer.data["name"],
        "picture": serializer.data.get("picture") or "",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }

    frontend_url = getattr(
        settings,
        "FRONTEND_AUTH_REDIRECT_URL",
        os.getenv("FRONTEND_AUTH_REDIRECT_URL")
    )
    return HttpResponseRedirect(f"{frontend_url}?{urlencode(query_params)}")

# class TodoView(APIView):
#     def get(self, request):
#         todos = Todo.objects.all()
#         serializer = TodoSerializer(todos, many=True)
#         return Response({"message": serializer.data})
    
#     def post(self, request):
#         serializer = TodoSerializer(data=request.data)
#         if serializer.is_valid():
#             todo = serializer.save()
#             return Response({"message": "Todo created successfully", "todo": serializer.data}, status=201)
#         return Response({"message": "Invalid data"}, status=400)


# class TodoView(viewsets.ModelViewSet):
#     queryset = Todo.objects.all()
#     serializer_class = TodoSerializer

def send_test_email():
    subject = "Hello from Django"
    message = "This is a test email sent using Django!"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    recipient_list = ["kallemk8@gmail.com"]

    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=True,
        )
        return True
    except Exception as exc:
        logger.exception("Failed to send test email: %s", exc)
        return False


@api_view(['GET'])
def todo_list(request):
    cached_todos = cache.get("todos")
    if cached_todos is not None:
        print("Returning cached todos")
        return Response(cached_todos)

    todos = Todo.objects.all()
    serializer = TodoSerializer(todos, many=True)
    print("Caching todos for 1 minute")
    cache.set("todos", serializer.data, timeout=60)  # Cache for 1 minute
    send_test_email()
    return Response(serializer.data)

@api_view(['GET'])
def user_list(request):
    cached_users = cache.get("users")
    if cached_users is not None:
        print("Returning cached users")
        return Response(cached_users)

    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    cache.set("users", serializer.data, timeout=60)  # Cache for 1 minute
    return Response(serializer.data)

"""
DRF provides these main API view types
@api_view (Function-Based View)
APIView
GenericAPIView
Mixins
Generic Views (ListAPIView, CreateAPIView, etc.)
ViewSet
ModelViewSet
ReadOnlyModelViewSet
    
"""

def google_auth(request):
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('REDIRECT_URI')
    scope = os.getenv('GOOGLE_SCOPE')
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"

    return HttpResponseRedirect(auth_url)


@api_view(['GET'])
def auth_user_list(request):
    AuthUser = get_user_model()
    users = AuthUser.objects.all()
    serializer = AuthUserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_user_register(request):
    data = request.data.copy()
    data.setdefault('username', data.get('name', data.get('email', '')))
    data.setdefault('email', data.get('email', ''))
    data.setdefault('password', 'admin@123')

    serializer = AuthUserRegisterSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        out = AuthUserSerializer(user)

        try:
            send_mail(
                subject="Welcome to Todo App",
                message=f"Hello {user.username}, thanks for registering with Todo App.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            pass

        return JsonResponse(out.data, status=201, safe=False)
    return JsonResponse(serializer.errors, status=400, safe=False)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def auth_user_login(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not password:
        return JsonResponse({"detail": "Password is required."}, status=400)

    AuthUser = get_user_model()

    # If email provided but not username, try to find username from email
    if email and not username:
        user_obj = AuthUser.objects.filter(email=email).first()
        if user_obj:
            username = getattr(user_obj, 'username', None)

    if not username:
        return JsonResponse({"detail": "Username or email is required."}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"detail": "Invalid credentials."}, status=401)

    tokens = create_user_tokens(user)
    serializer = AuthUserSerializer(user)
    return JsonResponse({"user": serializer.data, "tokens": tokens}, status=200, safe=False)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_access_token(request):
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return JsonResponse({"detail": "Refresh token is required."}, status=400)

    try:
        token = RefreshToken(refresh_token)
    except TokenError as exc:
        return JsonResponse({"detail": str(exc)}, status=401)

    payload = token.payload
    if payload.get("token_type") != "refresh":
        return JsonResponse({"detail": "Invalid refresh token type."}, status=401)

    user_id = payload.get("user_id")
    if not user_id:
        return JsonResponse({"detail": "Invalid refresh token payload."}, status=401)

    AuthUser = get_user_model()
    user = AuthUser.objects.filter(pk=user_id).first()
    if user is None:
        return JsonResponse({"detail": "User not found."}, status=401)

    tokens = create_user_tokens(user)
    return JsonResponse({"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]}, status=200)


@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return JsonResponse({"detail": "Email is required."}, status=400)

    AuthUser = get_user_model()
    user = AuthUser.objects.filter(email=email).first()

    if user is not None:
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password?email={email}&token={token}"
        try:
            send_mail(
                subject="Reset your password",
                message=f"Use this link to reset your password: {reset_link}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as exc:
            logger.exception("Failed to send reset email: %s", exc)

    return JsonResponse({"detail": "If an account exists for that email, a reset link has been sent."}, status=200)


@api_view(['POST'])
def reset_password(request):
    email = request.data.get('email')
    token = request.data.get('token')
    password = request.data.get('password')

    if not email or not token or not password:
        return JsonResponse({"detail": "Email, token, and password are required."}, status=400)

    AuthUser = get_user_model()
    user = AuthUser.objects.filter(email=email).first()
    if user is None or not default_token_generator.check_token(user, token):
        return JsonResponse({"detail": "Invalid or expired reset token."}, status=401)

    user.set_password(password)
    user.save()
    return JsonResponse({"detail": "Password reset successful."}, status=200)


@api_view(['GET', 'PUT', 'PATCH'])
def profile_detail(request):
    AuthUser = get_user_model()
    user = None

    if getattr(request, "user", None) and request.user.is_authenticated:
        user = request.user
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token, "tasks.auth.access")
            except ValueError:
                return JsonResponse({"detail": "Invalid or expired access token."}, status=401)

            user = AuthUser.objects.filter(pk=payload.get("user_id")).first()

    if user is None:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

    if request.method in ["PUT", "PATCH"]:
        serializer = AuthUserProfileSerializer(user, data=request.data, partial=request.method == "PATCH")
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)

    serializer = AuthUserProfileSerializer(user)
    return JsonResponse(serializer.data, status=200)


def google_callback(request):

    code = request.GET.get("code")

    token_url = "https://oauth2.googleapis.com/token"

    payload = {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_SECRET'),
        "code": code,
        "redirect_uri": os.getenv('REDIRECT_URI'),
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=payload)

    token_data = response.json()

    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers=headers
    )

    profile = user_info.json()
    password = "admin1234"  # Default password for new users; consider a more secure approach
    user_data = {
        "email": profile.get("email"),
        "name": profile.get("name"),
        "google_id": profile.get("id"),
        "picture": profile.get("picture"),
        'password': password  # Add the password to the user data
    }

    AuthUser = get_user_model()
    auth_user = AuthUser.objects.filter(email=user_data["email"]).first()
    if auth_user is None:
        auth_user = AuthUser.objects.filter(username=user_data["name"]).first()

    if auth_user is None:
        auth_user = AuthUser.objects.create_user(
            username=user_data["name"],
            email=user_data["email"],
            password=password,
        )
    else:
        if not auth_user.check_password(password):
            auth_user.set_password(password)
            auth_user.save(update_fields=["password"])

    existing_user = User.objects.filter(google_id=user_data["google_id"]).first()
    if existing_user:
        return redirect_to_frontend(
            existing_user,
            "User already exists. Login successful",
        )

    serializer = UserSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            send_mail(
                subject="Welcome to Todo App",
                message=f"Hello {user.name}, thanks for registering with Todo App via Google.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as exc:
            logger.exception("Failed to send Google signup email: %s", exc)
        return redirect_to_frontend(user, "User created successfully")

    return JsonResponse({"message": "Invalid user data"}, status=400)


class ExcelUploadAPIView(APIView):

    def post(self, request):

        serializer = ExcelUploadSerializer(data=request.data)

        if serializer.is_valid():

            excel_file = serializer.validated_data["file"]

            # Validate extension
            extension = os.path.splitext(excel_file.name)[1]

            if extension not in [".xlsx", ".xls"]:
                return Response(
                    {"error": "Only Excel files are allowed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_path = os.path.join(
                settings.MEDIA_ROOT,
                excel_file.name
            )

            # Save uploaded file
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            with open(file_path, "wb+") as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            # Read Excel
            try:

                if extension == ".xlsx":
                    df = pd.read_excel(file_path, engine="openpyxl")
                else:
                    df = pd.read_excel(file_path, engine="xlrd")

                data = df.to_dict(orient="records")

                return Response({
                    "success": True,
                    "total_records": len(data),
                    "data": data
                })

            except Exception as e:

                return Response(
                    {"error": str(e)},
                    status=500
                )

        return Response(serializer.errors, status=400)