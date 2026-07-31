from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import AccountProfile


def account_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return AccountProfile.Role.ROOT
    try:
        return user.account_profile.role
    except AccountProfile.DoesNotExist:
        return None


def is_root(user):
    return account_role(user) == AccountProfile.Role.ROOT


def is_admin(user):
    return account_role(user) == AccountProfile.Role.ADMIN


def can_review(user):
    return account_role(user) in {AccountProfile.Role.ROOT, AccountProfile.Role.ADMIN}


def root_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_root(request.user):
            raise PermissionDenied("只有 Root 可以管理账户权限。")
        return view_func(request, *args, **kwargs)

    return wrapped
