"""
Context processors - makes site settings available in ALL templates
"""
from django.conf import settings


def site_settings(request):
    """Inject site-wide settings into every template context."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Find Your Home Kenya'),
        'LANDLORD_FEE': getattr(settings, 'LANDLORD_FEE', 300),
        'TENANT_FEE': getattr(settings, 'TENANT_FEE', 100),
        'MPESA_TILL_NUMBER': getattr(settings, 'MPESA_TILL_NUMBER', ''),
    }
