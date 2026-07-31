from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

COMPANY_EMAIL_DOMAIN = "tp-link.com"


class AccountProfile(models.Model):
    class Role(models.TextChoices):
        ROOT = "root", "Root"
        ADMIN = "admin", "Admin"
        USER = "user", "User"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_profile",
    )
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("role", "email", "user__username")

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
            if self.email.rsplit("@", 1)[-1] != COMPANY_EMAIL_DOMAIN:
                raise ValidationError({"email": "仅支持 @tp-link.com 公司邮箱。"})
        if self.role == self.Role.ROOT and self.user.username != "root":
            raise ValidationError({"role": "Root 角色只能分配给默认 root 账户。"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
