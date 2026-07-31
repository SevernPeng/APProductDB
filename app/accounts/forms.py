from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import COMPANY_EMAIL_DOMAIN, AccountProfile


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="公司邮箱", max_length=150)
    password1 = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="确认密码",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email.rsplit("@", 1)[-1] != COMPANY_EMAIL_DOMAIN:
            raise ValidationError("仅支持 @tp-link.com 公司邮箱。")
        user_model = get_user_model()
        if (
            user_model.objects.filter(email__iexact=email).exists()
            or AccountProfile.objects.filter(email__iexact=email).exists()
        ):
            raise ValidationError("该邮箱已注册，请直接登录。")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "两次输入的密码不一致。")
        if password1:
            candidate = get_user_model()(username=cleaned.get("email", ""), email=cleaned.get("email", ""))
            try:
                password_validation.validate_password(password1, candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    @transaction.atomic
    def save(self):
        email = self.cleaned_data["email"]
        try:
            user = get_user_model().objects.create_user(
                username=email,
                email=email,
                password=self.cleaned_data["password1"],
            )
            AccountProfile.objects.create(
                user=user,
                email=email,
                role=AccountProfile.Role.USER,
            )
        except IntegrityError as exc:
            raise ValidationError("该邮箱已注册，请直接登录。") from exc
        return user


class RoleUpdateForm(forms.ModelForm):
    class Meta:
        model = AccountProfile
        fields = ("role",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = (
            (AccountProfile.Role.ADMIN, "Admin"),
            (AccountProfile.Role.USER, "User"),
        )
        self.fields["role"].widget.attrs["class"] = "form-select"

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in {AccountProfile.Role.ADMIN, AccountProfile.Role.USER}:
            raise ValidationError("只能在 Admin 和 User 之间调整权限。")
        return role
