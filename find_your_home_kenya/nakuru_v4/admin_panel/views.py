"""
Admin Panel - Views
Full control: users, listings, payments, settings
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone

from admin_panel.models import AdminUser
from admin_panel.decorators import admin_required
from landlords.models import Landlord, Property, PropertyPhoto
from tenants.models import Tenant
from payments.models import Payment, SiteSettings
from nakuru_houses.utils import hash_password, check_password


def login_view(request):
    """Admin login - the only way in."""
    if request.session.get('admin_logged_in'):
        return redirect('admin_panel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            admin = AdminUser.objects.get(username=username)
            if check_password(password, admin.password_hash):
                request.session['admin_logged_in'] = True
                request.session['admin_username'] = admin.username
                admin.last_login = timezone.now()
                admin.save(update_fields=['last_login'])
                return redirect('admin_panel:dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
        except AdminUser.DoesNotExist:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'admin_panel/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('admin_panel:login')


@admin_required
def dashboard(request):
    """Admin dashboard - overview of the whole platform."""
    stats = {
        'total_landlords': Landlord.objects.count(),
        'active_landlords': Landlord.objects.filter(is_active=True).count(),
        'total_tenants': Tenant.objects.count(),
        'active_tenants': Tenant.objects.filter(is_active=True).count(),
        'total_properties': Property.objects.count(),
        'approved_properties': Property.objects.filter(is_approved=True).count(),
        'pending_properties': Property.objects.filter(is_approved=False).count(),
        'total_payments': Payment.objects.filter(status='confirmed').count(),
        'total_revenue': Payment.objects.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or 0,
    }

    recent_payments = Payment.objects.filter(status='confirmed').order_by('-confirmed_at')[:10]
    pending_properties = Property.objects.filter(is_approved=False).select_related('landlord')[:10]
    recent_landlords = Landlord.objects.order_by('-joined_at')[:5]
    recent_tenants = Tenant.objects.order_by('-joined_at')[:5]

    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'recent_payments': recent_payments,
        'pending_properties': pending_properties,
        'recent_landlords': recent_landlords,
        'recent_tenants': recent_tenants,
    })


@admin_required
def landlords_list(request):
    """View and manage all landlords."""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    landlords = Landlord.objects.all()
    if search:
        landlords = landlords.filter(
            full_name__icontains=search
        ) | landlords.filter(email__icontains=search)
    if status == 'active':
        landlords = landlords.filter(is_active=True)
    elif status == 'inactive':
        landlords = landlords.filter(is_active=False)

    return render(request, 'admin_panel/landlords.html', {
        'landlords': landlords,
        'search': search,
        'status': status,
    })


@admin_required
def toggle_landlord_status(request, landlord_id):
    """Activate or deactivate a landlord account."""
    landlord = get_object_or_404(Landlord, id=landlord_id)
    landlord.is_active = not landlord.is_active
    landlord.save(update_fields=['is_active'])
    status = 'activated' if landlord.is_active else 'deactivated'
    messages.success(request, f'{landlord.full_name} has been {status}.')
    return redirect('admin_panel:landlords')


@admin_required
def delete_landlord(request, landlord_id):
    """Delete a landlord and all their listings."""
    landlord = get_object_or_404(Landlord, id=landlord_id)
    name = landlord.full_name
    if request.method == 'POST':
        landlord.delete()
        messages.success(request, f'Landlord "{name}" and all their listings deleted.')
    return redirect('admin_panel:landlords')


@admin_required
def tenants_list(request):
    """View and manage all tenants."""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    tenants = Tenant.objects.all()
    if search:
        tenants = tenants.filter(
            full_name__icontains=search
        ) | tenants.filter(email__icontains=search)
    if status == 'active':
        tenants = tenants.filter(is_active=True)
    elif status == 'inactive':
        tenants = tenants.filter(is_active=False)

    return render(request, 'admin_panel/tenants.html', {
        'tenants': tenants,
        'search': search,
        'status': status,
    })


@admin_required
def toggle_tenant_status(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant.is_active = not tenant.is_active
    tenant.save(update_fields=['is_active'])
    status = 'activated' if tenant.is_active else 'deactivated'
    messages.success(request, f'{tenant.full_name} has been {status}.')
    return redirect('admin_panel:tenants')


@admin_required
def listings(request):
    """View and manage all property listings."""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    properties = Property.objects.select_related('landlord').all()
    if status_filter == 'approved':
        properties = properties.filter(is_approved=True)
    elif status_filter == 'pending':
        properties = properties.filter(is_approved=False)
    if search:
        properties = properties.filter(title__icontains=search) | \
                     properties.filter(location__icontains=search)

    return render(request, 'admin_panel/listings.html', {
        'properties': properties,
        'status_filter': status_filter,
        'search': search,
    })


@admin_required
def approve_property(request, property_id):
    """Approve a property so it goes live."""
    prop = get_object_or_404(Property, id=property_id)
    prop.is_approved = True
    prop.save(update_fields=['is_approved'])
    messages.success(request, f'"{prop.title}" is now live.')
    return redirect('admin_panel:listings')


@admin_required
def reject_property(request, property_id):
    """Reject/unpublish a property."""
    prop = get_object_or_404(Property, id=property_id)
    prop.is_approved = False
    prop.save(update_fields=['is_approved'])
    messages.success(request, f'"{prop.title}" has been unpublished.')
    return redirect('admin_panel:listings')


@admin_required
def delete_property(request, property_id):
    """Permanently delete a property."""
    prop = get_object_or_404(Property, id=property_id)
    title = prop.title
    if request.method == 'POST':
        prop.delete()
        messages.success(request, f'Property "{title}" deleted.')
    return redirect('admin_panel:listings')


@admin_required
def payments_list(request):
    """View all payment records — pending ones shown first with confirm/reject buttons."""
    payments = Payment.objects.all().order_by('-created_at')
    pending_list = payments.filter(status='pending')
    confirmed_payments = payments.filter(status='confirmed').count()
    total_revenue = payments.filter(status='confirmed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'admin_panel/payments.html', {
        'payments': payments,
        'pending_list': pending_list,
        'total_payments': payments.count(),
        'pending_payments': pending_list.count(),
        'confirmed_payments': confirmed_payments,
        'total_revenue': total_revenue,
    })


@admin_required
def confirm_payment(request, payment_id):
    """Manually confirm a payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.status != 'confirmed':
        payment.confirm()
        # Activate the user
        from payments.views import _activate_user_after_payment
        _activate_user_after_payment(payment)
        messages.success(request, f'Payment confirmed and account activated.')
    return redirect('admin_panel:payments')


@admin_required
def site_settings(request):
    """Admin settings - change till number, fees, etc."""
    site = SiteSettings.get_settings()

    if request.method == 'POST':
        site.mpesa_till_number = request.POST.get('mpesa_till_number', site.mpesa_till_number).strip()
        site.landlord_fee = int(request.POST.get('landlord_fee', site.landlord_fee))
        site.tenant_fee = int(request.POST.get('tenant_fee', site.tenant_fee))
        site.site_name = request.POST.get('site_name', site.site_name).strip()
        site.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('admin_panel:settings')

    # Admin password change
    if request.POST.get('change_password'):
        current = request.POST.get('current_password', '')
        new_pass = request.POST.get('new_password', '')
        admin = AdminUser.objects.first()
        if admin and check_password(current, admin.password_hash):
            admin.password_hash = hash_password(new_pass)
            admin.save()
            messages.success(request, 'Password changed.')
        else:
            messages.error(request, 'Incorrect current password.')

    return render(request, 'admin_panel/settings.html', {'site': site})


@admin_required
def add_property_admin(request):
    """Admin can directly add/post a property on behalf of a landlord."""
    landlords = Landlord.objects.filter(is_active=True)

    if request.method == 'POST':
        landlord_id = request.POST.get('landlord_id')
        landlord = get_object_or_404(Landlord, id=landlord_id)

        prop = Property.objects.create(
            landlord=landlord,
            title=request.POST.get('title', '').strip(),
            property_type=request.POST.get('property_type', ''),
            price=int(request.POST.get('price', 0)),
            location=request.POST.get('location', '').strip(),
            address=request.POST.get('address', '').strip(),
            directions=request.POST.get('directions', '').strip(),
            description=request.POST.get('description', '').strip(),
            amenities=request.POST.get('amenities', '').strip(),
            contact_phone=request.POST.get('contact_phone', landlord.phone).strip(),
            contact_whatsapp=request.POST.get('contact_whatsapp', '').strip(),
            is_approved=True,  # Admin posts go live immediately
        )

        photos = request.FILES.getlist('photos')
        for i, photo in enumerate(photos[:10]):
            PropertyPhoto.objects.create(property=prop, image=photo, is_main=(i == 0))

        messages.success(request, f'Property "{prop.title}" posted and live.')
        return redirect('admin_panel:listings')

    return render(request, 'admin_panel/add_property.html', {
        'landlords': landlords,
        'property_types': Property.PROPERTY_TYPES,
    })
