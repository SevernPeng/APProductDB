from django.contrib import admin

from catalog.models import Brand

from .models import BenchmarkCase, ProductMatch


class OurProductBrandFilter(admin.SimpleListFilter):
    title = "our product brand"
    parameter_name = "our_brand"

    def lookups(self, request, model_admin):
        return Brand.objects.filter(active=True).values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(our_product__brand_id=self.value())
        return queryset


class CompetitorBrandFilter(admin.SimpleListFilter):
    title = "competitor brand"
    parameter_name = "competitor_brand"

    def lookups(self, request, model_admin):
        return Brand.objects.filter(active=True).values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(competitor_product__brand_id=self.value())
        return queryset


@admin.register(ProductMatch)
class ProductMatchAdmin(admin.ModelAdmin):
    list_display = (
        "our_product",
        "competitor_product",
        "benchmark_case",
        "match_type",
        "match_level",
        "status",
        "region",
        "match_score",
        "confidence",
        "rank",
        "updated_at",
    )
    list_filter = (
        "match_type",
        "match_level",
        "status",
        "region",
        OurProductBrandFilter,
        CompetitorBrandFilter,
    )
    search_fields = (
        "our_product__model",
        "competitor_product__model",
        "our_product__brand__name",
        "competitor_product__brand__name",
        "reason",
    )
    autocomplete_fields = (
        "our_product",
        "competitor_product",
        "benchmark_case",
        "reviewed_by",
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    list_select_related = (
        "our_product",
        "our_product__brand",
        "competitor_product",
        "competitor_product__brand",
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BenchmarkCase)
class BenchmarkCaseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "anchor_product",
        "region",
        "scenario",
        "template",
        "status",
        "updated_at",
    )
    list_filter = ("status", "region", "template")
    search_fields = ("name", "anchor_product__model", "scenario", "notes")
    autocomplete_fields = ("anchor_product", "template", "approved_by")
    readonly_fields = ("created_by", "created_at", "updated_at")
    list_select_related = ("anchor_product", "anchor_product__brand", "template")

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
