"""
Tenants App - Models
House hunters who browse and search listings
"""
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    """A person looking for a house in Nakuru."""
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False, help_text='Activated after subscription payment')
    joined_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class SavedProperty(models.Model):
    """Properties that a tenant has saved/bookmarked."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey('landlords.Property', on_delete=models.CASCADE)
    saved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('tenant', 'property')
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.tenant.full_name} saved {self.property.title}'
