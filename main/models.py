from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    phone = models.CharField(max_length=13,  null=True, blank=True)
    firebase_token = models.CharField(max_length=500, null=True, blank=True)
