
from django.urls import path

from tasks.views import  ExcelUploadAPIView, google_auth, google_callback, user_list, todo_list, google_authAPI
from tasks.views import auth_user_list, auth_user_register, auth_user_login

urlpatterns = [
    #path('todo/', TodoView.as_view(), name='todo-view'),

    path('todo/', todo_list, name='todo-list'),
    path('google-auth/', google_auth, name='google-auth'),
    path('users/', user_list, name='user-list'),
    path('auth-users/', auth_user_list, name='auth-user-list'),
    path('auth-users/register/', auth_user_register, name='auth-user-register'),
    path('auth-users/login/', auth_user_login, name='auth-user-login'),
    path('google-auth-api/', google_authAPI, name='google-auth-api'),
     path("upload-excel/", ExcelUploadAPIView.as_view()),
]
