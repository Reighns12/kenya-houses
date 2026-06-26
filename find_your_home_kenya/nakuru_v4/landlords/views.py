"""
Landlords App - Views
Register, login, pay, post property, manage listings
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from landlords.models import Landlord, Property, PropertyPhoto
from payments.models import SiteSettings
from nakuru_houses.utils import hash_password, check_password, landlord_login_required, landlord_active_required


def register(request):
    """Landlord registration page."""
    if request.session.get('landlord_id'):
        return redirect('landlords:dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validation
        errors = []
        if not all([full_name, email, phone, password]):
            errors.append('All fields are required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if Landlord.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if Landlord.objects.filter(phone=phone).exists():
            errors.append('This phone number is already registered.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'landlords/register.html', {'form_data': request.POST})

        # Create landlord (inactive until payment)
        landlord = Landlord.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            is_active=False,
        )
        request.session['landlord_id'] = landlord.id
        request.session['landlord_name'] = landlord.full_name
        messages.success(request, 'Account created! Complete payment to activate your account.')
        return redirect('landlords:payment')

    return render(request, 'landlords/register.html')


def login_view(request):
    """Landlord login."""
    if request.session.get('landlord_id'):
        return redirect('landlords:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            landlord = Landlord.objects.get(email=email)
            if check_password(password, landlord.password_hash):
                request.session['landlord_id'] = landlord.id
                request.session['landlord_name'] = landlord.full_name
                landlord.last_login = timezone.now()
                landlord.save(update_fields=['last_login'])

                if not landlord.is_active:
                    messages.warning(request, 'Please complete your payment to activate your account.')
                    return redirect('landlords:payment')

                return redirect('landlords:dashboard')
            else:
                messages.error(request, 'Incorrect email or password.')
        except Landlord.DoesNotExist:
            messages.error(request, 'No account found with that email.')

    return render(request, 'landlords/login.html')


def logout_view(request):
    """Log out landlord."""
    request.session.flush()
    return redirect('landlords:login')


def payment_page(request):
    """Payment page - shown to inactive landlords."""
    landlord_id = request.session.get('landlord_id')
    if not landlord_id:
        return redirect('landlords:login')

    try:
        landlord = Landlord.objects.get(id=landlord_id)
    except Landlord.DoesNotExist:
        return redirect('landlords:login')

    if landlord.is_active:
        return redirect('landlords:dashboard')

    site = SiteSettings.get_settings()
    return render(request, 'landlords/payment.html', {
        'landlord': landlord,
        'site': site,
        'amount': site.landlord_fee,
        'till_number': site.mpesa_till_number,
    })


@landlord_active_required
def dashboard(request):
    """Landlord dashboard - overview of their listings."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])
    properties = landlord.properties.all()
    approved = properties.filter(is_approved=True).count()
    pending = properties.filter(is_approved=False).count()

    return render(request, 'landlords/dashboard.html', {
        'landlord': landlord,
        'properties': properties[:6],
        'approved_count': approved,
        'pending_count': pending,
        'total_count': properties.count(),
    })


@landlord_active_required
def post_property(request):
    """Post a new property listing."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        property_type = request.POST.get('property_type', '')
        price = request.POST.get('price', 0)
        location = request.POST.get('location', '').strip()
        address = request.POST.get('address', '').strip()
        directions = request.POST.get('directions', '').strip()
        description = request.POST.get('description', '').strip()
        amenities = request.POST.get('amenities', '').strip()
        contact_phone = request.POST.get('contact_phone', landlord.phone).strip()
        contact_whatsapp = request.POST.get('contact_whatsapp', '').strip()

        errors = []
        if not all([title, property_type, price, location, address, description]):
            errors.append('Please fill in all required fields.')
        try:
            price = int(price)
            if price < 1:
                errors.append('Enter a valid price.')
        except (ValueError, TypeError):
            errors.append('Price must be a number.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'landlords/post_property.html', {
                'landlord': landlord,
                'form_data': request.POST,
            })

        property_obj = Property.objects.create(
            landlord=landlord,
            title=title,
            property_type=property_type,
            price=price,
            location=location,
            address=address,
            directions=directions,
            description=description,
            amenities=amenities,
            contact_phone=contact_phone,
            contact_whatsapp=contact_whatsapp,
            is_approved=False,  # Admin must approve
        )

        # Handle uploaded photos
        photos = request.FILES.getlist('photos')
        for i, photo in enumerate(photos[:10]):  # Max 10 photos
            PropertyPhoto.objects.create(
                property=property_obj,
                image=photo,
                is_main=(i == 0),
            )

        messages.success(request, 'Property submitted! It will be visible once approved by admin.')
        return redirect('landlords:my_properties')

    return render(request, 'landlords/post_property.html', {'landlord': landlord})


@landlord_active_required
def my_properties(request):
    """View all of the landlord's property listings."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])
    properties = landlord.properties.all()
    return render(request, 'landlords/my_properties.html', {
        'landlord': landlord,
        'properties': properties,
    })


@landlord_active_required
def edit_property(request, property_id):
    """Edit an existing property."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])
    property_obj = get_object_or_404(Property, id=property_id, landlord=landlord)

    if request.method == 'POST':
        property_obj.title = request.POST.get('title', property_obj.title).strip()
        property_obj.price = int(request.POST.get('price', property_obj.price))
        property_obj.location = request.POST.get('location', property_obj.location).strip()
        property_obj.address = request.POST.get('address', property_obj.address).strip()
        property_obj.directions = request.POST.get('directions', property_obj.directions).strip()
        property_obj.description = request.POST.get('description', property_obj.description).strip()
        property_obj.amenities = request.POST.get('amenities', property_obj.amenities).strip()
        property_obj.contact_phone = request.POST.get('contact_phone', property_obj.contact_phone).strip()
        property_obj.contact_whatsapp = request.POST.get('contact_whatsapp', property_obj.contact_whatsapp).strip()
        property_obj.is_approved = False  # Re-submit for approval after edit
        property_obj.save()

        # Handle new photos
        new_photos = request.FILES.getlist('photos')
        for photo in new_photos[:10]:
            PropertyPhoto.objects.create(property=property_obj, image=photo)

        messages.success(request, 'Property updated and submitted for re-approval.')
        return redirect('landlords:my_properties')

    return render(request, 'landlords/edit_property.html', {
        'landlord': landlord,
        'property': property_obj,
    })


@landlord_active_required
def delete_property(request, property_id):
    """Delete a property listing."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])
    property_obj = get_object_or_404(Property, id=property_id, landlord=landlord)
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted.')
    return redirect('landlords:my_properties')


@landlord_active_required
def profile(request):
    """Landlord profile page."""
    landlord = Landlord.objects.get(id=request.session['landlord_id'])

    if request.method == 'POST':
        landlord.full_name = request.POST.get('full_name', landlord.full_name).strip()
        landlord.phone = request.POST.get('phone', landlord.phone).strip()
        if 'profile_photo' in request.FILES:
            landlord.profile_photo = request.FILES['profile_photo']
        landlord.save()
        messages.success(request, 'Profile updated.')
        return redirect('landlords:profile')

    return render(request, 'landlords/profile.html', {'landlord': landlord})
