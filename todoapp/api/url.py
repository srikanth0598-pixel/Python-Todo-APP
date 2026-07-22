
from django.urls import path

from tasks.views import  ExcelUploadAPIView, google_auth, google_callback, user_list, todo_list
from tasks.views import auth_user_list, auth_user_register, auth_user_login, refresh_access_token, forgot_password, reset_password, profile_detail
from tasks.views import *

urlpatterns = [
    #path('todo/', TodoView.as_view(), name='todo-view'),

    path('todo/', todo_list, name='todo-list'),
    path('google-auth/', google_auth, name='google-auth'),
    path('users/', user_list, name='user-list'),
    path('auth-users/', auth_user_list, name='auth-user-list'),
    path('auth-users/register/', auth_user_register, name='auth-user-register'),
    path('auth-users/login/', auth_user_login, name='auth-user-login'),
    path('auth-users/refresh/', refresh_access_token, name='auth-user-refresh'),
    path('auth-users/forgot-password/', forgot_password, name='forgot-password'),
    path('auth-users/reset-password/', reset_password, name='reset-password'),
    path('profile/', profile_detail, name='profile-detail'),
    path("upload-excel/", ExcelUploadAPIView.as_view()),
    path(
        "todos/",
        TodoListAPIView.as_view()
    ),

    path(
        "todos/create/",
        TodoCreateAPIView.as_view()
    ),

    path(
        "todos/<int:pk>/",
        TodoDetailAPIView.as_view()
    ),

    path(
        "todos/<int:pk>/update/",
        TodoUpdateAPIView.as_view()
    ),

    path(
        "todos/<int:pk>/delete/",
        TodoDeleteAPIView.as_view()
    ),

    path(
        "todos/<int:pk>/status/",
        TodoStatusAPIView.as_view()
    ),

    path(
        "todos/<int:pk>/pin/",
        TodoPinAPIView.as_view()
    ),

    path(
        "todos/search/",
        TodoSearchAPIView.as_view()
    ),

    path(
        "categories/",
        CategoryListAPIView.as_view()
    ),

    path(
        "categories/create/",
        CategoryCreateAPIView.as_view()
    ),
]
