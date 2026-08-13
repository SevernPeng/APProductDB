from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from audit.models import AuditLog

from .forms import RegistrationForm
from .models import AccountProfile
from .permissions import root_required


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = form.save()
        except ValidationError as exc:
            form.add_error("email", exc)
        else:
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("home")
    return render(request, "registration/register.html", {"form": form})


@root_required
def account_list(request):
    profiles = AccountProfile.objects.select_related("user").order_by("role", "email")
    return render(request, "accounts/account_list.html", {"profiles": profiles})


@root_required
@require_POST
def delete_account(request, pk):
    profile = get_object_or_404(
        AccountProfile.objects.select_related("user"),
        pk=pk,
    )
    user = profile.user
    if user.username == "root" or profile.role == AccountProfile.Role.ROOT:
        messages.error(request, "The root account cannot be deleted.")
        return redirect("accounts:list")

    username = user.username
    with transaction.atomic():
        AuditLog.objects.create(
            actor=request.user,
            action="account.deleted",
            object_type=user._meta.label,
            object_id=str(user.pk),
            object_repr=username,
            before_data={
                "username": username,
                "email": user.email,
                "role": profile.role,
                "is_active": user.is_active,
            },
            after_data={"deleted": True},
            ip_address=(request.META.get("REMOTE_ADDR") or None),
        )
        user.delete()

    messages.success(request, f"Account {username} was deleted.")
    return redirect("accounts:list")
