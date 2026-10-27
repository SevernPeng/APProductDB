import re
import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def normalize_model_key(value):
    return re.sub(r"[\s\-_]+", "", value or "").upper()


def product_image_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()[:10]
    return f"products/{uuid.uuid4().hex}{suffix}"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Brand(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_own_brand = models.BooleanField(default=False)
    official_website = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def clean(self):
        super().clean()
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "A category cannot be its own parent."})

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name


class ProductType(TimestampedModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="product_types",
    )
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("category", "display_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("category", "code"),
                name="catalog_unique_category_product_type_code",
            ),
            models.UniqueConstraint(
                fields=("category", "name"),
                name="catalog_unique_category_product_type_name",
            ),
        ]

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class ProductModel(TimestampedModel):
    """Brand-owned model identity shared by regional/hardware variants."""

    class LifecycleStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        DISCONTINUED = "discontinued", "Discontinued"
        EOL = "eol", "EOL"

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="product_models",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="product_models",
    )
    model = models.CharField(max_length=150, db_index=True)
    model_key = models.CharField(max_length=150, db_index=True, editable=False)
    series = models.CharField(max_length=150, blank=True)
    product_name = models.CharField(max_length=250, blank=True)
    positioning = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    lifecycle_status = models.CharField(
        max_length=20,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
        db_index=True,
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("brand__name", "model")
        constraints = [
            models.UniqueConstraint(
                fields=("brand", "model_key"),
                name="catalog_unique_brand_product_model",
            )
        ]

    def save(self, *args, **kwargs):
        self.model_key = normalize_model_key(self.model)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.model}"


class Product(TimestampedModel):
    class APType(models.TextChoices):
        CEILING = "ceiling", "Ceiling"
        WALL = "wall", "Wall"
        WALL_PLATE = "wall_plate", "Wall Plate"
        OUTDOOR = "outdoor", "Outdoor"
        DESKTOP = "desktop", "Desktop"
        OTHER = "other", "Other"

    class LifecycleStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        DISCONTINUED = "discontinued", "Discontinued"
        EOL = "eol", "EOL"

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    product_type = models.ForeignKey(
        ProductType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Category-specific form factor or management layer.",
    )
    product_model = models.ForeignKey(
        ProductModel,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="variants",
        help_text="Canonical model identity. Populated automatically for new records.",
    )
    model = models.CharField(max_length=150, db_index=True)
    model_key = models.CharField(max_length=150, db_index=True, editable=False)
    region = models.CharField(max_length=50, default="US", db_index=True)
    hardware_version = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=150, blank=True)
    nom_records = models.JSONField(default=list, blank=True, editable=False)
    ap_type = models.CharField(
        max_length=20,
        choices=APType.choices,
        blank=True,
        default="",
        db_index=True,
    )
    wifi_standard = models.CharField(max_length=50, blank=True, default="")
    lifecycle_status = models.CharField(
        max_length=20,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
    )
    official_url = models.URLField(blank=True)
    launch_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to=product_image_upload_to, blank=True)
    notes = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_updated",
    )

    class Meta:
        ordering = ("brand__name", "model", "region", "hardware_version")
        constraints = [
            models.UniqueConstraint(
                fields=("brand", "model_key", "region", "hardware_version"),
                name="catalog_unique_product_version",
            )
        ]

    def clean(self):
        super().clean()
        if self.product_type_id and self.product_type.category_id != self.category_id:
            raise ValidationError(
                {"product_type": "Product type must belong to the selected category."}
            )
        if self.product_model_id:
            errors = {}
            if self.product_model.brand_id != self.brand_id:
                errors["brand"] = "Brand must match the canonical product model."
            if self.product_model.category_id != self.category_id:
                errors["category"] = "Category must match the canonical product model."
            if self.product_model.model_key != normalize_model_key(self.model):
                errors["model"] = "Model must match the canonical product model."
            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.model_key = normalize_model_key(self.model)
        if not self.product_model_id and self.brand_id and self.category_id and self.model:
            self.full_clean()
            self.product_model, _ = ProductModel.objects.get_or_create(
                brand=self.brand,
                model_key=self.model_key,
                defaults={
                    "category": self.category,
                    "model": self.model,
                    "lifecycle_status": self.lifecycle_status,
                },
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        version = f" {self.hardware_version}" if self.hardware_version else ""
        return f"{self.brand} {self.model} ({self.region}{version})"

    @property
    def has_nom(self):
        from .nom import has_current_nom

        return has_current_nom(self.nom_records)

    @property
    def aggregate_rate_mbps(self):
        rate_codes = ("rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps")
        cached_specs = getattr(self, "_prefetched_objects_cache", {}).get("specs")
        if cached_specs is None:
            values = self.specs.filter(definition__code__in=rate_codes).values_list(
                "value_number", flat=True
            )
        else:
            values = (
                spec.value_number
                for spec in cached_specs
                if spec.definition.code in rate_codes
            )
        return sum((value or Decimal("0") for value in values), Decimal("0"))


class PriceSource(TimestampedModel):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    base_url = models.URLField()
    active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, blank=True)
    last_sync_message = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ProductPriceListing(TimestampedModel):
    source = models.ForeignKey(
        PriceSource,
        on_delete=models.PROTECT,
        related_name="product_listings",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_listings",
    )
    external_id = models.CharField(max_length=100)
    external_model = models.CharField(max_length=200)
    product_url = models.URLField()
    active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("source", "product")
        constraints = [
            models.UniqueConstraint(
                fields=("source", "product"),
                name="catalog_unique_product_price_listing",
            ),
        ]
        indexes = [
            models.Index(
                fields=("source", "external_id"),
                name="catalog_price_external_idx",
            ),
        ]

    def __str__(self):
        return f"{self.product} · {self.source} · {self.external_model}"


class ProductPriceSnapshot(TimestampedModel):
    source = models.ForeignKey(
        PriceSource,
        on_delete=models.PROTECT,
        related_name="price_snapshots",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_snapshots",
    )
    external_id = models.CharField(max_length=100, blank=True)
    external_model = models.CharField(max_length=200)
    product_url = models.URLField()
    currency = models.CharField(max_length=3, default="USD")
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    list_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    special_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    tax_included = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("product", "source", "-created_at"), name="catalog_price_product_idx"),
        ]

    def __str__(self):
        return f"{self.product} · {self.source} · {self.currency} {self.unit_price}"


class SpecDefinition(TimestampedModel):
    class DataType(models.TextChoices):
        TEXT = "text", "Text"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Boolean"
        CHOICE = "choice", "Choice"

    class ComparisonDirection(models.TextChoices):
        HIGHER = "higher", "Higher is better"
        LOWER = "lower", "Lower is better"
        EQUAL = "equal", "Equality/support comparison"
        NONE = "none", "No automatic comparison"

    code = models.SlugField(max_length=100, unique=True)
    display_name = models.CharField(max_length=150)
    group = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="spec_definitions",
    )
    data_type = models.CharField(max_length=20, choices=DataType.choices)
    unit = models.CharField(max_length=50, blank=True)
    is_filterable = models.BooleanField(default=False)
    is_core = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    collection_rule = models.TextField(blank=True)
    comparison_direction = models.CharField(
        max_length=20,
        choices=ComparisonDirection.choices,
        default=ComparisonDirection.NONE,
    )
    is_derived = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "display_name")

    def __str__(self):
        return self.display_name


class ProductSpec(TimestampedModel):
    class ValueStatus(models.TextChoices):
        PUBLISHED = "published", "Published"
        NOT_PUBLISHED = "not_published", "Not Published"
        NOT_APPLICABLE = "not_applicable", "Not Applicable"
        UNKNOWN = "unknown", "Unknown"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    definition = models.ForeignKey(SpecDefinition, on_delete=models.PROTECT)
    value_status = models.CharField(
        max_length=20,
        choices=ValueStatus.choices,
        default=ValueStatus.PUBLISHED,
        db_index=True,
    )
    value_text = models.TextField(blank=True)
    value_number = models.DecimalField(
        null=True,
        blank=True,
        max_digits=14,
        decimal_places=3,
    )
    value_boolean = models.BooleanField(null=True, blank=True)
    normalized_value = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    raw_value = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    source_note = models.TextField(blank=True)
    verified_date = models.DateField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_specs_updated",
    )

    class Meta:
        ordering = ("product", "definition__display_order")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "definition"),
                name="catalog_unique_product_spec",
            )
        ]

    def clean(self):
        super().clean()
        populated_values = sum(
            (
                bool((self.value_text or "").strip()),
                self.value_number is not None,
                self.value_boolean is not None,
            )
        )
        if populated_values > 1:
            raise ValidationError(
                "A specification can populate only one typed value column."
            )
        if self.value_status != self.ValueStatus.PUBLISHED and populated_values:
            raise ValidationError(
                "Only published specifications may contain a typed value."
            )
        if self.value_status == self.ValueStatus.PUBLISHED and populated_values:
            expected_types = {
                SpecDefinition.DataType.TEXT: "text",
                SpecDefinition.DataType.CHOICE: "text",
                SpecDefinition.DataType.INTEGER: "number",
                SpecDefinition.DataType.DECIMAL: "number",
                SpecDefinition.DataType.BOOLEAN: "boolean",
            }
            actual_type = (
                "text"
                if bool((self.value_text or "").strip())
                else "number"
                if self.value_number is not None
                else "boolean"
            )
            expected_type = expected_types.get(self.definition.data_type)
            if expected_type and actual_type != expected_type:
                raise ValidationError(
                    f"{self.definition.display_name} requires a {expected_type} value."
                )
            if (
                self.definition.data_type == SpecDefinition.DataType.INTEGER
                and self.value_number is not None
                and self.value_number != self.value_number.to_integral_value()
            ):
                raise ValidationError(
                    f"{self.definition.display_name} requires a whole number."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def display_value(self):
        if self.value_status != self.ValueStatus.PUBLISHED:
            return self.get_value_status_display()
        if self.value_number is not None:
            value = format(self.value_number, "f")
            if "." in value:
                value = value.rstrip("0").rstrip(".")
            if value in {"", "-0"}:
                value = "0"
            return f"{value} {self.unit or self.definition.unit}".strip()
        if self.value_boolean is not None:
            return "Yes" if self.value_boolean else "No"
        return self.value_text or "Unknown"

    @property
    def effective_source_url(self):
        return self.source_url or self.product.official_url

    def __str__(self):
        return f"{self.product}: {self.definition} = {self.display_value}"


class SourceDocument(TimestampedModel):
    class DocumentType(models.TextChoices):
        PRODUCT_PAGE = "product_page", "Product page"
        SPECIFICATION = "specification", "Specification page"
        DATASHEET = "datasheet", "Datasheet"
        WHITE_PAPER = "white_paper", "White paper"
        CATALOG = "catalog", "Catalog"
        SUPPORT = "support", "Support document"
        OTHER = "other", "Other"

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="source_documents",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="source_documents",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    title = models.CharField(max_length=250)
    url = models.URLField(max_length=500, blank=True)
    file = models.FileField(upload_to="source-documents/", blank=True)
    region = models.CharField(max_length=50, blank=True)
    document_version = models.CharField(max_length=100, blank=True)
    published_date = models.DateField(null=True, blank=True)
    accessed_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("brand__name", "title")
        constraints = [
            models.UniqueConstraint(
                fields=("url", "document_version"),
                name="catalog_unique_source_document_version",
            )
        ]

    def __str__(self):
        return self.title


class SpecEvidence(TimestampedModel):
    class EvidenceLevel(models.TextChoices):
        A = "a", "A - Specification/datasheet"
        B = "b", "B - Official product page"
        C = "c", "C - Official catalog/support"

    product_spec = models.ForeignKey(
        ProductSpec,
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.PROTECT,
        related_name="spec_evidence",
    )
    source_location = models.CharField(max_length=250, blank=True)
    source_excerpt = models.TextField(blank=True)
    evidence_level = models.CharField(
        max_length=1,
        choices=EvidenceLevel.choices,
        default=EvidenceLevel.B,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spec_evidence_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("product_spec", "evidence_level", "source_document")
        constraints = [
            models.UniqueConstraint(
                fields=("product_spec", "source_document", "source_location"),
                name="catalog_unique_spec_evidence_location",
            )
        ]

    def __str__(self):
        return f"{self.product_spec} [{self.get_evidence_level_display()}]"


class ProductHighlight(TimestampedModel):
    class HighlightType(models.TextChoices):
        PERFORMANCE = "performance", "Performance"
        COVERAGE = "coverage", "Coverage"
        CAPACITY = "capacity", "Capacity"
        DEPLOYMENT = "deployment", "Deployment"
        SECURITY = "security", "Security"
        MANAGEMENT = "management", "Management"
        OTHER = "other", "Other"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="highlights",
    )
    highlight_type = models.CharField(max_length=20, choices=HighlightType.choices)
    headline = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    quantified_claim = models.CharField(max_length=250, blank=True)
    comparison_baseline = models.CharField(max_length=250, blank=True)
    claim_conditions = models.TextField(blank=True)
    source_document = models.ForeignKey(
        SourceDocument,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="product_highlights",
    )
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("product", "display_order", "id")

    def __str__(self):
        return f"{self.product}: {self.headline}"


class ComparisonTemplate(TimestampedModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="comparison_templates",
    )
    form_factor = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=150)
    version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("category", "form_factor", "name", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("category", "form_factor", "name", "version"),
                name="catalog_unique_comparison_template_version",
            )
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class TemplateField(TimestampedModel):
    class Priority(models.TextChoices):
        P0 = "p0", "P0 - Required core"
        P1 = "p1", "P1 - Important"
        P2 = "p2", "P2 - Extended"

    template = models.ForeignKey(
        ComparisonTemplate,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    spec_definition = models.ForeignKey(
        SpecDefinition,
        on_delete=models.PROTECT,
        related_name="template_fields",
    )
    priority = models.CharField(max_length=2, choices=Priority.choices)
    required = models.BooleanField(default=False)
    display_group = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    highlight_relevance = models.BooleanField(default=False)

    class Meta:
        ordering = ("template", "display_order", "spec_definition")
        constraints = [
            models.UniqueConstraint(
                fields=("template", "spec_definition"),
                name="catalog_unique_template_spec_definition",
            )
        ]

    def __str__(self):
        return f"{self.template}: {self.spec_definition}"
