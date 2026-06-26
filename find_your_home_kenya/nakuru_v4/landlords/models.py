"""
Landlords App - Models
"""
from django.db import models
from django.utils import timezone


class Landlord(models.Model):
    """A landlord who lists apartments on the platform."""
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False, help_text='Activated after payment')
    joined_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='landlords/photos/', blank=True, null=True)

    class Meta:
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def property_count(self):
        return self.properties.filter(is_approved=True).count()


class Property(models.Model):
    """An apartment or house listed by a landlord."""
    PROPERTY_TYPES = [
        ('bedsitter', 'Bedsitter'),
        ('single', 'Single Room'),
        ('1bedroom', '1 Bedroom'),
        ('2bedroom', '2 Bedroom'),
        ('3bedroom', '3 Bedroom'),
        ('4bedroom', '4+ Bedroom'),
        ('studio', 'Studio'),
        ('bungalow', 'Bungalow'),
    ]

    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    price = models.PositiveIntegerField(help_text='Monthly rent in KSh')
    location = models.CharField(max_length=200, help_text='Estate / area in Nakuru')
    address = models.TextField(help_text='Full address details')
    directions = models.TextField(help_text='Directions to reach the property')
    description = models.TextField()
    amenities = models.TextField(blank=True, help_text='Comma-separated: Water, Electricity, WiFi...')
    contact_phone = models.CharField(max_length=15)
    contact_whatsapp = models.CharField(max_length=15, blank=True)
    is_approved = models.BooleanField(default=False, help_text='Admin approves before going live')
    is_available = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f'{self.title} - {self.location} ({self.get_property_type_display()})'

    def get_main_photo(self):
        photo = self.photos.filter(is_main=True).first()
        if not photo:
            photo = self.photos.first()
        return photo

    def get_amenities_list(self):
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',') if a.strip()]
        return []


class PropertyPhoto(models.Model):
    """Photos for a property - multiple photos per property."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='properties/%Y/%m/')
    caption = models.CharField(max_length=100, blank=True)
    is_main = models.BooleanField(default=False, help_text='Main cover photo')
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-is_main', 'uploaded_at']

    def __str__(self):
        return f'Photo for {self.property.title}'
