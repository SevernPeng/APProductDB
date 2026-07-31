from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from catalog.models import ComparisonTemplate, Product, TimestampedModel


class BenchmarkCase(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEWED = "reviewed", "Reviewed"
        APPROVED = "approved", "Approved"

    anchor_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="benchmark_cases",
    )
    template = models.ForeignKey(
        ComparisonTemplate,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="benchmark_cases",
    )
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=50, default="US", db_index=True)
    scenario = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="benchmark_cases_created",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="benchmark_cases_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("anchor_product", "region", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("anchor_product", "region", "name"),
                name="comparison_unique_benchmark_case_name",
            )
        ]

    def clean(self):
        super().clean()
        if self.anchor_product_id and not self.anchor_product.brand.is_own_brand:
            raise ValidationError(
                {"anchor_product": "The benchmark anchor must belong to an own brand."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductMatch(TimestampedModel):
    class MatchType(models.TextChoices):
        DIRECT = "direct", "Direct"
        PERFORMANCE = "performance", "Performance"
        PRICE = "price", "Price"
        FUNCTION = "function", "Function"
        CANDIDATE = "candidate", "Candidate"

    class MatchLevel(models.TextChoices):
        CORE = "core", "Core competitor"
        SECONDARY = "secondary", "Secondary competitor"
        ALTERNATIVE = "alternative", "Alternative"

    class Status(models.TextChoices):
        CANDIDATE = "candidate", "Candidate"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"

    our_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="competitor_matches",
    )
    competitor_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="matched_as_competitor",
    )
    benchmark_case = models.ForeignKey(
        BenchmarkCase,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    match_type = models.CharField(max_length=20, choices=MatchType.choices)
    match_level = models.CharField(
        max_length=20,
        choices=MatchLevel.choices,
        default=MatchLevel.CORE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CANDIDATE,
        db_index=True,
    )
    region = models.CharField(max_length=50, default="US")
    match_score = models.PositiveSmallIntegerField(null=True, blank=True)
    rank = models.PositiveSmallIntegerField(default=0)
    confidence = models.PositiveSmallIntegerField(null=True, blank=True)
    reason = models.TextField(blank=True)
    advantages = models.TextField(blank=True)
    disadvantages = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches_reviewed",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches_updated",
    )

    class Meta:
        ordering = ("our_product", "rank", "competitor_product", "region")
        verbose_name = "product match"
        verbose_name_plural = "product matches"
        constraints = [
            models.UniqueConstraint(
                fields=("our_product", "competitor_product", "region"),
                condition=Q(benchmark_case__isnull=True),
                name="comparison_unique_legacy_product_match",
            ),
            models.UniqueConstraint(
                fields=("benchmark_case", "competitor_product"),
                condition=Q(benchmark_case__isnull=False),
                name="comparison_unique_case_competitor",
            ),
            models.CheckConstraint(
                condition=~Q(our_product=F("competitor_product")),
                name="comparison_prevent_self_match",
            ),
        ]

    def clean(self):
        super().clean()
        if self.our_product_id and self.competitor_product_id:
            if self.our_product_id == self.competitor_product_id:
                raise ValidationError("A product cannot be matched to itself.")
            if not self.our_product.brand.is_own_brand:
                raise ValidationError(
                    {"our_product": "Our product must belong to an own brand."}
                )
        if self.benchmark_case_id and self.our_product_id:
            if self.benchmark_case.anchor_product_id != self.our_product_id:
                raise ValidationError(
                    {"benchmark_case": "Benchmark case anchor must match our product."}
                )
            if self.benchmark_case.region != self.region:
                raise ValidationError(
                    {"region": "Match region must equal the benchmark case region."}
                )
        if self.match_score is not None and self.match_score > 100:
            raise ValidationError({"match_score": "Match score must be between 0 and 100."})
        if self.confidence is not None and self.confidence > 100:
            raise ValidationError({"confidence": "Confidence must be between 0 and 100."})
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError({"valid_to": "Valid-to date cannot precede valid-from."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.our_product} -> {self.competitor_product}"
