"""Custom decorators for access control in the library_web app"""

from django.http import HttpResponse
from django.shortcuts import redirect

def unauthenticated_user(view_func):
    """Restrict access to views for authenticated users"""
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_users(allowed_roles=None):
    """Restrict access to views based on user roles."""
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if 'superuser' in allowed_roles and request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if 'admin' in allowed_roles and request.user.username == 'admin':
                return view_func(request, *args, **kwargs)
            return HttpResponse("You are not authorised to view this page")
        return wrapper_func
    return decorator
