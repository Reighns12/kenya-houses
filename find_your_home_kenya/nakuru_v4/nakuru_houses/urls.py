"""
Find Your Home Kenya - Main URL Configuration
All routes split cleanly per section
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

# The admin path is secret - stored in settings, not visible in code
ADMIN_PATH = getattr(settings, 'ADMIN_SECRET_PATH', 'control-hub-x9z')

urlpatterns = [
    # Tenants (public-facing - the main site)
    path('', include('tenants.urls')),

    # Landlords
    path('landlords/', include('landlords.urls')),

    # Payments
    path('payments/', include('payments.urls')),

    # HIDDEN ADMIN - path comes from settings, not hardcoded here
    path(f'{ADMIN_PATH}/', include('admin_panel.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
