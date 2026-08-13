from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

COMPANY_EMAIL_DOMAIN = "tp-link.com"


class AccountProfile(models.Model):
    class Role(models.TextChoices):
        ROOT = "root", "Root"
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
        constraints = [
            models.UniqueConstraint(
                fields=("role",),
                condition=models.Q(role="root"),
                name="accounts_single_root_profile",
            )
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
            if self.email.rsplit("@", 1)[-1] != COMPANY_EMAIL_DOMAIN:
                raise ValidationError({"email": "Only @tp-link.com company email addresses are supported."})
        if self.user.username == "root" and self.role != self.Role.ROOT:
            raise ValidationError({"role": "The default root account must retain the Root role."})
        if self.role == self.Role.ROOT and self.user.username != "root":
            raise ValidationError({"role": "The Root role is reserved for the default root account."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
