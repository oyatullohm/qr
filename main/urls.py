from django.urls import path
from .views import api_register, api_login

urlpatterns = [
    path('register/', api_register, name='api_register'),
    path('login/', api_login, name='api_login'),
]
