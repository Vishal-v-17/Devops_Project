from django.http import HttpResponse 
from django.shortcuts import redirect

def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):

            # ✔ Allow superuser if requested
            if 'superuser' in allowed_roles and request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # ✔ If "admin" is in allowed_roles → allow username = "admin"
            if 'admin' in allowed_roles and request.user.username == 'admin':
                return view_func(request, *args, **kwargs)

            # ❌ Not allowed
            return HttpResponse("You are not authorised to view this page")

        return wrapper_func
    return decorator

