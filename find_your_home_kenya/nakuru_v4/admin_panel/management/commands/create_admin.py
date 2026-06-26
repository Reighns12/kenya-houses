"""
Management command: create_admin
Run: python manage.py create_admin

Creates the super admin account from .env credentials.
"""
import os
from django.core.management.base import BaseCommand
from admin_panel.models import AdminUser
from nakuru_houses.utils import hash_password
from payments.models import SiteSettings


class Command(BaseCommand):
    help = 'Create the admin user and initialize site settings'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD', 'change_this_now')
        email = os.getenv('ADMIN_EMAIL', 'admin@nakuruhouses.com')
        till = os.getenv('MPESA_TILL_NUMBER', '')
        landlord_fee = int(os.getenv('LANDLORD_FEE', '300'))
        tenant_fee = int(os.getenv('TENANT_FEE', '100'))

        # Create or update admin
        admin, created = AdminUser.objects.get_or_create(username=username)
        admin.password_hash = hash_password(password)
        admin.email = email
        admin.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user "{username}" created.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Admin user "{username}" already exists — password updated.'))

        # Initialize site settings
        site, _ = SiteSettings.objects.get_or_create(pk=1)
        site.mpesa_till_number = till
        site.landlord_fee = landlord_fee
        site.tenant_fee = tenant_fee
        site.save()

        self.stdout.write(self.style.SUCCESS(f'✅ Site settings initialized.'))
        self.stdout.write(self.style.SUCCESS(f'   Till: {till or "(not set — update in admin settings)"}'))
        self.stdout.write(self.style.SUCCESS(f'   Landlord fee: KSh {landlord_fee}'))
        self.stdout.write(self.style.SUCCESS(f'   Tenant fee: KSh {tenant_fee}'))
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('🚀 Setup complete! Run: python manage.py runserver'))
