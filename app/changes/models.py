from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Product, ProductSpec
from comparison.models import ProductMatch

from .validators import change_attachment_upload_to, validate_change_attachment


class ChangeRequest(models.Model):
    class RequestType(models.TextChoices):
        PRODUCT = "product", "Product"
        SPEC = "spec", "Specification"
        MATCH = "match", "Match"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    target_product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    target_spec = models.ForeignKey(
        ProductSpec,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    target_match = models.ForeignKey(
        ProductMatch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    field_name = models.CharField(max_length=150)
    old_value = models.JSONField(default=dict)
    proposed_value = models.JSONField(default=dict)
    reason = models.TextField()
    source_url = models.URLField(blank=True)
    attachment = models.FileField(
        upload_to=change_attachment_upload_to,
        validators=[validate_change_attachment],
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="change_requests",
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_changes",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)

    class Meta:
        ordering = ("-submitted_at", "-pk")

    def clean(self):
        super().clean()
        if self.request_type == self.RequestType.PRODUCT:
            valid = self.target_product_id and not self.target_spec_id and not self.target_match_id
        elif self.request_type == self.RequestType.SPEC:
            valid = self.target_spec_id and not self.target_match_id
            if valid and self.target_product_id != self.target_spec.product_id:
                valid = False
        elif self.request_type == self.RequestType.MATCH:
            if self.field_name == "__add__":
                valid = (
                    self.target_product_id
                    and not self.target_spec_id
                    and not self.target_match_id
                )
            else:
                valid = self.target_match_id and not self.target_spec_id
                if valid and self.target_product_id != self.target_match.our_product_id:
                    valid = False
        else:
            valid = False
        if not valid:
            raise ValidationError("申请类型与目标对象不一致。")
        if not self.reason.strip():
            raise ValidationError({"reason": "修改原因不能为空。"})
        if self.old_value == self.proposed_value:
            raise ValidationError({"proposed_value": "建议值不能与当前值相同。"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def product(self):
        if self.target_product_id:
            return self.target_product
        if self.target_spec_id:
            return self.target_spec.product
        if self.target_match_id:
            return self.target_match.our_product
        return None

    def __str__(self):
        return f"#{self.pk or 'new'} {self.field_name} ({self.status})"
