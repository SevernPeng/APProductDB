from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import RegistrationForm, RoleUpdateForm
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
            messages.success(request, "账户注册成功。当前角色为 User。")
            return redirect("home")
    return render(request, "registration/register.html", {"form": form})


@root_required
def account_list(request):
    profiles = AccountProfile.objects.select_related("user").order_by("role", "email")
    return render(request, "accounts/account_list.html", {"profiles": profiles})


@root_required
@require_POST
def update_role(request, pk):
    profile = get_object_or_404(AccountProfile.objects.select_related("user"), pk=pk)
    if profile.role == AccountProfile.Role.ROOT or profile.user.is_superuser:
        messages.error(request, "默认 Root 账户的角色不可修改。")
        return redirect("accounts:list")
    form = RoleUpdateForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, f"{profile.email} 已调整为 {profile.get_role_display()}。")
    else:
        messages.error(request, "角色调整失败。")
    return redirect("accounts:list")
