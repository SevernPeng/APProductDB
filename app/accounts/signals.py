from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import AccountProfile


@receiver(pre_save, sender=get_user_model())
def enforce_single_root(sender, instance, **kwargs):
    is_root = instance.username == "root"
    instance.is_staff = is_root
    instance.is_superuser = is_root


@receiver(post_save, sender=get_user_model())
def ensure_account_profile(sender, instance, **kwargs):
    role = AccountProfile.Role.ROOT if instance.username == "root" else AccountProfile.Role.USER
    email = (instance.email or "").strip().lower() or None
    if email and not email.endswith("@tp-link.com"):
        email = None
    if email and AccountProfile.objects.filter(email=email).exclude(user=instance).exists():
        email = None
    AccountProfile.objects.update_or_create(
        user=instance,
        defaults={"email": email, "role": role},
    )
