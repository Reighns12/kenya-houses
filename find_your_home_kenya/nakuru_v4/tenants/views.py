"""
Tenants App - Views
Landing page, registration, login, browse listings (public preview + subscribed full view)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from tenants.models import Tenant, SavedProperty
from landlords.models import Property
from payments.models import SiteSettings
from nakuru_houses.utils import hash_password, check_password, tenant_login_required, tenant_active_required


def landing(request):
    """The beautiful public landing page - visible to everyone."""
    sample_properties = Property.objects.filter(is_approved=True, is_available=True)[:6]
    site = SiteSettings.get_settings()
    total_listings = Property.objects.filter(is_approved=True, is_available=True).count()
    return render(request, 'tenants/landing.html', {
        'sample_properties': sample_properties,
        'total_listings': total_listings,
        'site': site,
    })


def browse(request):
    """
    PUBLIC browse page — anyone can see houses (type + price only).
    No location, no contact, no address shown.
    Search by type and max price only.
    """
    property_type = request.GET.get('type', '')
    max_price = request.GET.get('max_price', '')

    properties = Property.objects.filter(is_approved=True, is_available=True)

    if property_type:
        properties = properties.filter(property_type=property_type)
    if max_price:
        try:
            properties = properties.filter(price__lte=int(max_price))
        except ValueError:
            pass

    site = SiteSettings.get_settings()

    return render(request, 'tenants/browse.html', {
        'properties': properties,
        'property_types': Property.PROPERTY_TYPES,
        'selected_type': property_type,
        'selected_max_price': max_price,
        'total': properties.count(),
        'site': site,
        'is_logged_in': bool(request.session.get('tenant_id')),
        'is_active': _is_tenant_active(request),
    })


def property_preview(request, property_id):
    """
    Public preview of a single property — type, size, price, photos only.
    After clicking SELECT, user is redirected to login/subscribe.
    """
    prop = get_object_or_404(Property, id=property_id, is_approved=True, is_available=True)
    site = SiteSettings.get_settings()

    # If tenant is active, redirect straight to full detail
    if _is_tenant_active(request):
        return redirect('tenants:property_detail', property_id=property_id)

    return render(request, 'tenants/property_preview.html', {
        'property': prop,
        'photos': prop.photos.all(),
        'site': site,
        'is_logged_in': bool(request.session.get('tenant_id')),
    })


def register(request):
    """Tenant registration."""
    if request.session.get('tenant_id'):
        return redirect('tenants:home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []
        if not all([full_name, email, phone, password]):
            errors.append('All fields are required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if Tenant.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if Tenant.objects.filter(phone=phone).exists():
            errors.append('This phone number is already registered.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'tenants/register.html', {'form_data': request.POST})

        tenant = Tenant.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            is_active=False,
        )
        request.session['tenant_id'] = tenant.id
        request.session['tenant_name'] = tenant.full_name

        # If they came from a property preview, redirect back after payment
        next_property = request.GET.get('next_property', '')
        if next_property:
            request.session['next_property'] = next_property

        messages.success(request, 'Account created! Subscribe to view full property details.')
        return redirect('tenants:payment')

    return render(request, 'tenants/register.html', {
        'next_property': request.GET.get('next_property', ''),
    })


def login_view(request):
    """Tenant login."""
    if request.session.get('tenant_id'):
        tenant_id = request.session['tenant_id']
        try:
            t = Tenant.objects.get(id=tenant_id)
            if t.is_active:
                return redirect('tenants:home')
        except Tenant.DoesNotExist:
            pass

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            tenant = Tenant.objects.get(email=email)
            if check_password(password, tenant.password_hash):
                request.session['tenant_id'] = tenant.id
                request.session['tenant_name'] = tenant.full_name
                tenant.last_login = timezone.now()
                tenant.save(update_fields=['last_login'])

                if not tenant.is_active:
                    messages.warning(request, 'Please subscribe to activate your account.')
                    return redirect('tenants:payment')

                # Redirect back to property if they came from preview
                next_property = request.GET.get('next_property', '')
                if next_property:
                    return redirect('tenants:property_detail', property_id=next_property)

                return redirect('tenants:home')
            else:
                messages.error(request, 'Incorrect email or password.')
        except Tenant.DoesNotExist:
            messages.error(request, 'No account found with that email.')

    return render(request, 'tenants/login.html', {
        'next_property': request.GET.get('next_property', ''),
    })


def logout_view(request):
    request.session.flush()
    return redirect('tenants:landing')


def payment_page(request):
    """Subscription payment page for tenants."""
    tenant_id = request.session.get('tenant_id')
    if not tenant_id:
        return redirect('tenants:login')

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return redirect('tenants:login')

    if tenant.is_active:
        next_property = request.session.pop('next_property', '')
        if next_property:
            return redirect('tenants:property_detail', property_id=next_property)
        return redirect('tenants:home')

    site = SiteSettings.get_settings()
    return render(request, 'tenants/payment.html', {
        'tenant': tenant,
        'site': site,
        'amount': site.tenant_fee,
        'till_number': site.mpesa_till_number,
    })


@tenant_active_required
def home(request):
    """Main listings page for subscribed tenants — full details visible."""
    tenant = Tenant.objects.get(id=request.session['tenant_id'])
    property_type = request.GET.get('type', '')
    location = request.GET.get('location', '')
    max_price = request.GET.get('max_price', '')

    properties = Property.objects.filter(is_approved=True, is_available=True)

    if property_type:
        properties = properties.filter(property_type=property_type)
    if location:
        properties = properties.filter(location__icontains=location)
    if max_price:
        try:
            properties = properties.filter(price__lte=int(max_price))
        except ValueError:
            pass

    saved_ids = set(tenant.saved_properties.values_list('property_id', flat=True))

    return render(request, 'tenants/home.html', {
        'tenant': tenant,
        'properties': properties,
        'saved_ids': saved_ids,
        'property_types': Property.PROPERTY_TYPES,
        'selected_type': property_type,
        'selected_location': location,
        'selected_max_price': max_price,
        'total': properties.count(),
    })


@tenant_active_required
def property_detail(request, property_id):
    """Full details page — only for subscribed tenants."""
    tenant = Tenant.objects.get(id=request.session['tenant_id'])
    property_obj = get_object_or_404(Property, id=property_id, is_approved=True)

    Property.objects.filter(id=property_id).update(views_count=property_obj.views_count + 1)

    is_saved = tenant.saved_properties.filter(property=property_obj).exists()

    similar = Property.objects.filter(
        is_approved=True,
        is_available=True,
        property_type=property_obj.property_type
    ).exclude(id=property_obj.id)[:4]

    return render(request, 'tenants/property_detail.html', {
        'tenant': tenant,
        'property': property_obj,
        'photos': property_obj.photos.all(),
        'amenities': property_obj.get_amenities_list(),
        'is_saved': is_saved,
        'similar': similar,
    })


@tenant_active_required
def toggle_save(request, property_id):
    """Save or unsave a property."""
    tenant = Tenant.objects.get(id=request.session['tenant_id'])
    property_obj = get_object_or_404(Property, id=property_id, is_approved=True)

    saved, created = SavedProperty.objects.get_or_create(tenant=tenant, property=property_obj)
    if not created:
        saved.delete()
        return JsonResponse({'saved': False})

    return JsonResponse({'saved': True})


@tenant_active_required
def saved_properties(request):
    """Tenant's saved/bookmarked properties."""
    tenant = Tenant.objects.get(id=request.session['tenant_id'])
    saved = tenant.saved_properties.select_related('property').all()
    return render(request, 'tenants/saved.html', {
        'tenant': tenant,
        'saved': saved,
    })


@tenant_active_required
def profile(request):
    """Tenant profile."""
    tenant = Tenant.objects.get(id=request.session['tenant_id'])

    if request.method == 'POST':
        tenant.full_name = request.POST.get('full_name', tenant.full_name).strip()
        tenant.phone = request.POST.get('phone', tenant.phone).strip()
        tenant.save()
        messages.success(request, 'Profile updated.')
        return redirect('tenants:profile')

    return render(request, 'tenants/profile.html', {'tenant': tenant})


# ── Helper ──────────────────────────────────────────────────────────────────
def _is_tenant_active(request):
    tenant_id = request.session.get('tenant_id')
    if not tenant_id:
        return False
    try:
        return Tenant.objects.get(id=tenant_id).is_active
    except Tenant.DoesNotExist:
        return False
