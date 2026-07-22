from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.authentication import  JWTAuthentication

@api_view(['GET'])

@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def protected_view(request):
    return Response({"message": f"Hello {request.user.username}, you are authenticated!"})


@csrf_exempt
def login_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # creates session + sets cookie
            return JsonResponse({"message": "Login successful"})
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)

def logout_api(request):
    logout(request)  # clears session
    return JsonResponse({"message": "Logged out successfully"})
