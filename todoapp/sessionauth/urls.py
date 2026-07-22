
from django.urls import path, include
from .views import protected_view, login_api, logout_api
urlpatterns = [
    
    path("protected-view/", protected_view),
     path("login/", login_api, name="login_api"),
    path("logout/", logout_api, name="logout_api"),
    
]