"""
Admin Panel - Models
Stores admin credentials securely
"""
from django.db import models
from django.utils import timezone


class AdminUser(models.Model):
    """The single admin account - only you."""
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.EmailField()
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Admin: {self.username}'
