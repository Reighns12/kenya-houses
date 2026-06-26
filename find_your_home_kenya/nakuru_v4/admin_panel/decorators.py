"""
Admin Panel - Decorators
Protects all admin views - only authenticated admin can access
"""
from functools import wraps
from django.shortcuts import redirect


def admin_required(view_func):
    """Decorator: blocks anyone who is not the logged-in admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            return redirect('admin_panel:login')
        return view_func(request, *args, **kwargs)
    return wrapper
