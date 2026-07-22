from django.urls import include, path
from rest_framework import routers
#from tasks.views import TodoView
router = routers.DefaultRouter()
router.register(r'todo', TodoView, basename='todo')

urlpatterns = [
    path('', include(router.urls)),
]