from django.db import migrations, models


def normalize_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    AccountProfile = apps.get_model("accounts", "AccountProfile")

    for user in User.objects.all():
        email = (user.email or "").strip().lower()
        if (
            not email.endswith("@tp-link.com")
            or AccountProfile.objects.filter(email=email).exclude(user=user).exists()
        ):
            email = None
        AccountProfile.objects.update_or_create(
            user=user,
            defaults={
                "email": email,
                "role": "root" if user.username == "root" else "user",
            },
        )
    AccountProfile.objects.exclude(user__username="root").update(role="user")
    AccountProfile.objects.filter(user__username="root").update(role="root")
    User.objects.exclude(username="root").update(is_staff=False, is_superuser=False)
    User.objects.filter(username="root").update(
        is_active=True,
        is_staff=True,
        is_superuser=True,
    )
    Group.objects.filter(name__in=("Viewer", "Contributor")).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_account_profile")]

    operations = [
        migrations.RunPython(normalize_accounts, noop_reverse),
        migrations.AlterField(
            model_name="accountprofile",
            name="role",
            field=models.CharField(
                choices=[("root", "Root"), ("user", "User")],
                default="user",
                max_length=10,
            ),
        ),
        migrations.AddConstraint(
            model_name="accountprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("role", "root")),
                fields=("role",),
                name="accounts_single_root_profile",
            ),
        ),
    ]
