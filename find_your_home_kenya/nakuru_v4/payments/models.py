"""
Payments App - Models
Handles M-Pesa transactions and admin-configurable till number
"""
from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    """Admin-controlled settings - till number, fees, etc."""
    mpesa_till_number = models.CharField(max_length=20, default='', help_text='Your M-Pesa Till Number')
    landlord_fee = models.PositiveIntegerField(default=300, help_text='One-time fee for landlords (KSh)')
    tenant_fee = models.PositiveIntegerField(default=100, help_text='One-time fee for tenants (KSh)')
    site_name = models.CharField(max_length=100, default='Find Your Home Kenya')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Site Settings'

    def __str__(self):
        return f'Site Settings (Till: {self.mpesa_till_number})'

    @classmethod
    def get_settings(cls):
        """Always returns the first (and only) settings object."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Payment(models.Model):
    """Records every payment made on the platform."""
    PAYMENT_TYPE_CHOICES = [
        ('landlord', 'Landlord Registration'),
        ('tenant', 'Tenant Subscription'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    user_phone = models.CharField(max_length=15)
    user_email = models.CharField(max_length=255, blank=True)
    amount = models.PositiveIntegerField()
    mpesa_code = models.CharField(max_length=20, blank=True, help_text='M-Pesa transaction code')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.payment_type} | {self.user_phone} | KSh {self.amount} | {self.status}'

    def confirm(self):
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
