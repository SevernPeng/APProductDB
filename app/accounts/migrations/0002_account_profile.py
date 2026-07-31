from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def seed_root_account(apps, schema_editor):
    User = apps.get_model("auth", "User")
    AccountProfile = apps.get_model("accounts", "AccountProfile")
    for existing_user in User.objects.exclude(username="root"):
        role = "admin" if existing_user.is_superuser else "user"
        email = (existing_user.email or "").strip().lower()
        if not email.endswith("@tp-link.com") or AccountProfile.objects.filter(email=email).exists():
            email = None
        AccountProfile.objects.get_or_create(
            user=existing_user,
            defaults={"email": email, "role": role},
        )
        if existing_user.is_superuser or existing_user.is_staff:
            existing_user.is_superuser = False
            existing_user.is_staff = False
            existing_user.save(update_fields=["is_superuser", "is_staff"])
    root, _ = User.objects.get_or_create(
        username="root",
        defaults={"is_staff": True, "is_superuser": True, "is_active": True},
    )
    root.is_staff = True
    root.is_superuser = True
    root.is_active = True
    root.password = make_password("Nqt1_Ulk0")
    root.save()
    AccountProfile.objects.update_or_create(
        user=root,
        defaults={"email": None, "role": "root"},
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_create_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(blank=True, max_length=150, null=True, unique=True)),
                ("role", models.CharField(choices=[("root", "Root"), ("admin", "Admin"), ("user", "User")], default="user", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="account_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("role", "email", "user__username")},
        ),
        migrations.RunPython(seed_root_account, migrations.RunPython.noop),
    ]
