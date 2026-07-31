import changes.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
        ("comparison", "0002_alter_productmatch_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChangeRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_type", models.CharField(choices=[("product", "Product"), ("spec", "Specification"), ("match", "Match")], max_length=20)),
                ("field_name", models.CharField(max_length=150)),
                ("old_value", models.JSONField(default=dict)),
                ("proposed_value", models.JSONField(default=dict)),
                ("reason", models.TextField()),
                ("source_url", models.URLField(blank=True)),
                ("attachment", models.FileField(blank=True, upload_to=changes.validators.change_attachment_upload_to, validators=[changes.validators.validate_change_attachment])),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], db_index=True, default="pending", max_length=20)),
                ("submitted_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_comment", models.TextField(blank=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_changes", to=settings.AUTH_USER_MODEL)),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="change_requests", to=settings.AUTH_USER_MODEL)),
                ("target_match", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="change_requests", to="comparison.productmatch")),
                ("target_product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="change_requests", to="catalog.product")),
                ("target_spec", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="change_requests", to="catalog.productspec")),
            ],
            options={"ordering": ("-submitted_at", "-pk")},
        )
    ]
