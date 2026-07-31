from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import AccountProfile
from accounts.permissions import account_role, can_review

CATALOG_GROUPS = ("Viewer", "Contributor")


def can_view_catalog(user):
    return bool(
        user.is_authenticated
        and (
            account_role(user) in AccountProfile.Role.values
            or user.groups.filter(name__in=CATALOG_GROUPS).exists()
        )
    )


def can_contribute(user):
    return bool(
        user.is_authenticated
        and (
            account_role(user) in AccountProfile.Role.values
            or user.groups.filter(name="Contributor").exists()
        )
    )


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
            raise PermissionDenied("Your account cannot submit change requests.")
        return view_func(request, *args, **kwargs)

    return wrapped


def superuser_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only administrators can review change requests.")
        return view_func(request, *args, **kwargs)

    return wrapped


def reviewer_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not can_review(request.user):
            raise PermissionDenied("只有 Admin 或 Root 可以审核修改申请。")
        return view_func(request, *args, **kwargs)

    return wrapped
