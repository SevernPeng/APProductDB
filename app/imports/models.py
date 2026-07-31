import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def import_source_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    uploaded_at = instance.uploaded_at or timezone.now()
    return f"imports/source/{uploaded_at:%Y/%m}/{uuid.uuid4().hex}{suffix}"


def import_error_upload_to(instance, filename):
    uploaded_at = instance.uploaded_at or timezone.now()
    return f"imports/errors/{uploaded_at:%Y/%m}/{uuid.uuid4().hex}.csv"


class ImportJob(models.Model):
    class Mode(models.TextChoices):
        PREVIEW = "preview", "Preview only"
        CREATE_ONLY = "create_only", "Create only"
        CREATE_UPDATE = "create_update", "Create and update"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        VALIDATING = "validating", "Validating"
        INVALID = "invalid", "Invalid"
        READY = "ready", "Ready"
        IMPORTED = "imported", "Imported"
        FAILED = "failed", "Failed"

    uploaded_file = models.FileField(upload_to=import_source_upload_to)
    product_type = models.ForeignKey(
        "catalog.ProductType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="import_jobs",
        help_text="Product form selected before downloading and uploading a template.",
    )
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.PREVIEW)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    error_report = models.FileField(upload_to=import_error_upload_to, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="import_jobs",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def clean(self):
        super().clean()
        if self.uploaded_file and Path(self.uploaded_file.name).suffix.lower() != ".xlsx":
            raise ValidationError({"uploaded_file": "Only .xlsx files are supported."})

    def __str__(self):
        return f"Import #{self.pk or 'new'} - {self.get_status_display()}"
