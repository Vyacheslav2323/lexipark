from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    country = models.CharField(max_length=64, blank=True, default='')

    def __str__(self):
        return f"{self.user.username}"

# Create your models here.
