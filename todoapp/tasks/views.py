# pyrefly: ignore [missing-import]
from datetime import timedelta
import secrets
from urllib.parse import urlencode

from django.conf import settings
from  django.core.cache import cache
from django.core import signing
from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Todo, User
from django.http import HttpResponseRedirect
from .serializers import (
    TodoSerializer,
    UserSerializer,
    ExcelUploadSerializer,
    AuthUserSerializer,
    AuthUserRegisterSerializer,
)
from django.contrib.auth import get_user_model, authenticate
import os
import pandas as pd
from rest_framework import status
import requests
from django.http import JsonResponse
from dotenv import load_dotenv
load_dotenv()
# Create your views here.

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


def create_user_tokens(user):
    now = timezone.now()

    # Safely access attributes that may not exist on all user models
    user_id = getattr(user, "id", None)
    email = getattr(user, "email", "")
    google_id = getattr(user, "google_id", "")

    access_payload = {
        "token_type": "access",
        "user_id": user_id,
        "email": email,
        "google_id": google_id,
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TOKEN_LIFETIME).timestamp()),
    }
    refresh_payload = {
        "token_type": "refresh",
        "user_id": user_id,
        "email": email,
        "google_id": google_id,
        "iat": int(now.timestamp()),
        "jti": secrets.token_urlsafe(16),
        "exp": int((now + REFRESH_TOKEN_LIFETIME).timestamp()),
    }

    return {
        "access_token": signing.dumps(
            access_payload,
            salt="tasks.auth.access",
        ),
        "refresh_token": signing.dumps(
            refresh_payload,
            salt="tasks.auth.refresh",
        ),
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
def auth_user_register(request):
    serializer = AuthUserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        out = AuthUserSerializer(user)
        return JsonResponse(out.data, status=201, safe=False)
    return JsonResponse(serializer.errors, status=400, safe=False)


@api_view(['POST'])
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

    existing_user = User.objects.filter(google_id=user_data["google_id"]).first()
    if existing_user:
        return redirect_to_frontend(
            existing_user,
            "User already exists. Login successful",
        )

    serializer = UserSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        return redirect_to_frontend(user, "User created successfully")
    

    return JsonResponse({"message": "Invalid user data"}, status=400)


@api_view(["POST"])
def google_authAPI(request):
    user_data = request.data

    existing_user = User.objects.filter(
        google_id=user_data["google_id"]
    ).first()

    if existing_user:
        return redirect_to_frontend(
            existing_user,
            "User already exists. Login successful",
        )

    serializer = UserSerializer(data=user_data)

    if serializer.is_valid():
        user = serializer.save()
        return JsonResponse(user, "User created successfully")

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