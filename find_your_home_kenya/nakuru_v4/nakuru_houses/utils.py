"""
Shared utilities - password hashing, session helpers, etc.
"""
import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash a password with a salt using SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()
    return f'{salt}:{hashed}'


def check_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, hashed = stored_hash.split(':', 1)
        check = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()
        return check == hashed
    except Exception:
        return False


def landlord_login_required(view_func):
    """Decorator to require landlord login."""
    from functools import wraps
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('landlord_id'):
            return redirect('landlords:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def landlord_active_required(view_func):
    """Decorator to require landlord login AND active subscription."""
    from functools import wraps
    from django.shortcuts import redirect
    from landlords.models import Landlord

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        landlord_id = request.session.get('landlord_id')
        if not landlord_id:
            return redirect('landlords:login')
        try:
            landlord = Landlord.objects.get(id=landlord_id)
            if not landlord.is_active:
                return redirect('landlords:payment')
        except Landlord.DoesNotExist:
            return redirect('landlords:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_login_required(view_func):
    """Decorator to require tenant login."""
    from functools import wraps
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('tenant_id'):
            return redirect('tenants:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_active_required(view_func):
    """Decorator to require tenant login AND active subscription."""
    from functools import wraps
    from django.shortcuts import redirect
    from tenants.models import Tenant

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant_id = request.session.get('tenant_id')
        if not tenant_id:
            return redirect('tenants:login')
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            if not tenant.is_active:
                return redirect('tenants:payment')
        except Tenant.DoesNotExist:
            return redirect('tenants:login')
        return view_func(request, *args, **kwargs)
    return wrapper
