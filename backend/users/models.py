from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default='student')
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    subscription_status = models.BooleanField(default=False)
    subscription_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
