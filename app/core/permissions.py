from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def can_view_catalog(user):
    return bool(user.is_authenticated)


def can_contribute(user):
    return bool(user.is_authenticated)


def catalog_access_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not can_view_catalog(request.user):
            raise PermissionDenied("Your account does not have catalog access.")
        return view_func(request, *args, **kwargs)

    return wrapped


def contributor_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not can_contribute(request.user):
            raise PermissionDenied("Your account cannot modify catalog data.")
        return view_func(request, *args, **kwargs)

    return wrapped
