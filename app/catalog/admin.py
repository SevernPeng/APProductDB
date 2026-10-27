from django.contrib import admin

from .models import (
    Brand,
    Category,
    ComparisonTemplate,
    Product,
    ProductHighlight,
    ProductModel,
    ProductPriceListing,
    ProductPriceSnapshot,
    ProductSpec,
    ProductType,
    PriceSource,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
    TemplateField,
)


@admin.register(PriceSource)
class PriceSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "active", "last_synced_at", "last_sync_status")
    list_filter = ("active", "last_sync_status")
    search_fields = ("name", "code", "base_url")
    readonly_fields = ("last_synced_at", "last_sync_status", "last_sync_message", "created_at", "updated_at")


@admin.register(ProductPriceSnapshot)
class ProductPriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ("product", "source", "currency", "unit_price", "list_price", "special_price", "created_at")
    list_filter = ("source", "currency", "tax_included", "created_at")
    search_fields = ("product__model", "external_model", "external_id")
    autocomplete_fields = ("product", "source")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("product", "product__brand", "source")


@admin.register(ProductPriceListing)
class ProductPriceListingAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "source",
        "external_id",
        "external_model",
        "active",
        "last_seen_at",
        "last_checked_at",
    )
    list_filter = ("source", "active")
    search_fields = ("product__model", "external_model", "external_id")
    autocomplete_fields = ("product", "source")
    readonly_fields = ("created_at", "updated_at", "last_seen_at", "last_checked_at")
    list_select_related = ("product", "product__brand", "source")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_own_brand", "active", "updated_at")
    list_filter = ("is_own_brand", "active")
    search_fields = ("name", "slug", "official_website")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "active", "updated_at")
    list_filter = ("active", "parent")
    search_fields = ("name", "slug", "parent__name")
    autocomplete_fields = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "active", "display_order", "updated_at")
    list_filter = ("category", "active")
    search_fields = ("name", "code", "description", "category__name")
    autocomplete_fields = ("category",)
    list_editable = ("active", "display_order")
    ordering = ("category", "display_order", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SpecDefinition)
class SpecDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "code",
        "group",
        "category",
        "data_type",
        "unit",
        "is_core",
        "is_filterable",
        "comparison_direction",
        "is_derived",
        "active",
        "display_order",
    )
    list_filter = (
        "category",
        "group",
        "data_type",
        "comparison_direction",
        "is_core",
        "is_filterable",
        "is_derived",
        "active",
    )
    search_fields = ("code", "display_name", "description", "collection_rule")
    list_editable = ("is_core", "is_filterable", "is_derived", "active", "display_order")
    ordering = ("display_order", "display_name")
    readonly_fields = ("created_at", "updated_at")


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 0
    autocomplete_fields = ("definition",)
    fields = (
        "definition",
        "value_status",
        "value_text",
        "value_number",
        "value_boolean",
        "normalized_value",
        "unit",
        "raw_value",
        "source_url",
        "verified_date",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "product_model",
        "product_type",
        "brand",
        "region",
        "hardware_version",
        "ap_type",
        "lifecycle_status",
        "is_published",
        "updated_at",
    )
    list_filter = (
        "brand",
        "category",
        "product_type",
        "ap_type",
        "region",
        "lifecycle_status",
        "is_published",
    )
    search_fields = (
        "model",
        "model_key",
        "product_model__model",
        "brand__name",
        "region",
        "hardware_version",
        "sku",
    )
    autocomplete_fields = ("brand", "category", "product_model", "product_type")
    readonly_fields = ("model_key", "created_at", "updated_at", "created_by", "updated_by")
    list_select_related = ("brand", "category")
    inlines = (ProductSpecInline,)
    fieldsets = (
        ("Identity", {"fields": ("product_model", "brand", "category", "product_type", "model", "model_key")} ),
        ("Version", {"fields": ("region", "hardware_version", "sku", "ap_type", "wifi_standard", "launch_date")} ),
        ("Lifecycle", {"fields": ("lifecycle_status", "is_published")} ),
        ("Source", {"fields": ("official_url", "image", "notes")} ),
        ("Audit", {"fields": ("created_by", "updated_by", "created_at", "updated_at")} ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for deleted_object in formset.deleted_objects:
            deleted_object.delete()
        for instance in instances:
            if isinstance(instance, ProductSpec):
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(ProductSpec)
class ProductSpecAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "definition",
        "value_status",
        "display_value",
        "verified_date",
        "updated_at",
    )
    list_filter = ("value_status", "definition__group", "definition", "verified_date")
    search_fields = (
        "product__model",
        "product__brand__name",
        "definition__display_name",
        "value_text",
        "raw_value",
    )
    autocomplete_fields = ("product", "definition")
    readonly_fields = ("created_at", "updated_at", "updated_by")
    list_select_related = ("product", "product__brand", "definition")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "brand",
        "category",
        "series",
        "lifecycle_status",
        "active",
        "updated_at",
    )
    list_filter = ("brand", "category", "lifecycle_status", "active")
    search_fields = ("model", "model_key", "product_name", "series", "brand__name")
    autocomplete_fields = ("brand", "category")
    readonly_fields = ("model_key", "created_at", "updated_at")
    list_select_related = ("brand", "category")


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "brand",
        "document_type",
        "region",
        "document_version",
        "accessed_date",
        "active",
    )
    list_filter = ("brand", "document_type", "region", "active")
    search_fields = ("title", "url", "document_version", "product__model")
    autocomplete_fields = ("brand", "product")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SpecEvidence)
class SpecEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "product_spec",
        "source_document",
        "evidence_level",
        "source_location",
        "verified_at",
    )
    list_filter = ("evidence_level", "source_document__document_type")
    search_fields = (
        "product_spec__product__model",
        "product_spec__definition__display_name",
        "source_document__title",
        "source_location",
    )
    autocomplete_fields = ("product_spec", "source_document", "verified_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProductHighlight)
class ProductHighlightAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "highlight_type",
        "headline",
        "quantified_claim",
        "display_order",
    )
    list_filter = ("highlight_type",)
    search_fields = ("product__model", "headline", "description", "quantified_claim")
    autocomplete_fields = ("product", "source_document")
    list_editable = ("display_order",)
    readonly_fields = ("created_at", "updated_at")


class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 0
    autocomplete_fields = ("spec_definition",)


@admin.register(ComparisonTemplate)
class ComparisonTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "form_factor", "version", "active", "updated_at")
    list_filter = ("category", "form_factor", "active")
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    inlines = (TemplateFieldInline,)
    readonly_fields = ("created_at", "updated_at")


@admin.register(TemplateField)
class TemplateFieldAdmin(admin.ModelAdmin):
    list_display = (
        "template",
        "spec_definition",
        "priority",
        "required",
        "display_group",
        "display_order",
        "weight",
    )
    list_filter = ("template", "priority", "required", "highlight_relevance")
    search_fields = ("template__name", "spec_definition__display_name", "display_group")
    autocomplete_fields = ("template", "spec_definition")
    list_editable = ("priority", "required", "display_order")
    readonly_fields = ("created_at", "updated_at")
