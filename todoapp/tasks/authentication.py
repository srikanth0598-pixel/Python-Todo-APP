from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
        except Exception as exc:
            raise AuthenticationFailed("Invalid or expired access token") from exc

        user_id = validated_token.payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid access token payload")

        AuthUser = get_user_model()
        user = AuthUser.objects.filter(pk=user_id).first()
        if user is None:
            raise AuthenticationFailed("User not found")

        return user, None
