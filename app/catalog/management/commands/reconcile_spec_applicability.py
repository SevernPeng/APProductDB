from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, ProductSpec, ProductType
from catalog.product_types import (
    infer_managed_switch_poe,
    infer_product_type_code,
    infer_switch_management_type,
    product_type_code,
)
from catalog.services import template_fields
from catalog.spec_applicability import (
    POE_OUTPUT_SPEC_CODES,
    field_is_applicable,
    has_published_value,
    specs_by_code,
    switch_has_management_features,
    switch_poe_state,
)


class Command(BaseCommand):
    help = (
        "Rebuild product specification placeholders from type-specific templates "
        "and remove empty rows that are not applicable to the product."
    )

    def add_arguments(self, parser):
        parser.add_argument("--brand", action="append", dest="brands")
        parser.add_argument("--category", action="append", dest="categories")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        products = Product.objects.select_related(
            "brand", "category", "product_type", "product_model"
        ).prefetch_related("specs__definition", "specs__evidence")
        if options["brands"]:
            products = products.filter(brand__name__in=options["brands"])
        if options["categories"]:
            products = products.filter(category__slug__in=options["categories"])

        created = 0
        deleted = 0
        preserved_extra_values = 0
        reclassified = 0
        for product in products:
            current = specs_by_code(product)
            current_type = product_type_code(product)
            legacy_switch_family = {
                "l2": "l2",
                "l2_plus": "l2",
                "l3": "l3",
            }.get(current_type, "")
            management_spec = current.get("management_type")
            management_value = (
                management_spec.value_text
                if has_published_value(management_spec)
                else ""
            )
            has_management_features = switch_has_management_features(current)
            feature_text = " ".join(
                spec.display_value
                for code, spec in current.items()
                if code in {
                    "l3_features",
                    "routing_entry_capacity",
                    "ospf_support",
                    "rip_support",
                    "pbr_support",
                    "vrrp_support",
                }
                and has_published_value(spec)
            )
            explicit_type = infer_switch_management_type(
                management_value,
                has_management_features,
            )
            should_reinfer = current_type in {
                "",
                "other",
                "unknown",
                "l2",
                "l2_plus",
                "l3",
                "unmanaged",
                "easy_smart",
            } or (
                product.category.slug == "accessories"
                and current_type == "antenna"
                and product.model.upper().startswith("APM")
            ) or (
                product.category.slug == "unmanaged-easy-smart-switches"
                and explicit_type
                and not current_type.startswith(f"{explicit_type}_")
            )
            if should_reinfer:
                model_poe = infer_managed_switch_poe(
                    product.brand.name,
                    product.model,
                    getattr(product.product_model, "product_name", ""),
                )
                inferred_type = infer_product_type_code(
                    product.category.slug,
                    product.model,
                    product.ap_type,
                    management_value,
                    has_management_features,
                    has_poe=(
                        model_poe
                        if model_poe is not None
                        else switch_poe_state(product, current)
                    ),
                    switch_family=legacy_switch_family,
                    product_name=getattr(product.product_model, "product_name", ""),
                    brand_name=product.brand.name,
                    feature_text=feature_text,
                )
                if inferred_type not in {"", "other", "unknown"}:
                    product.product_type = ProductType.objects.get(
                        category=product.category,
                        code=inferred_type,
                        active=True,
                    )
                    product.save(update_fields=("product_type", "updated_at"))
                    reclassified += 1
            applicable_codes = {
                field.spec_definition.code
                for field in template_fields(
                    product.category, product_type_code(product)
                )
                if field.spec_definition.active
                and field_is_applicable(product, field.spec_definition.code, current)
            }
            for code, spec in current.items():
                if code in applicable_codes:
                    continue
                if (
                    code in POE_OUTPUT_SPEC_CODES
                    and switch_poe_state(product, current) is False
                ):
                    spec.delete()
                    deleted += 1
                    continue
                has_value = bool(
                    spec.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        (spec.value_text or "").strip()
                        or spec.value_number is not None
                        or spec.value_boolean is not None
                    )
                )
                if has_value:
                    preserved_extra_values += 1
                    continue
                spec.delete()
                deleted += 1

            remaining_codes = set(
                product.specs.values_list("definition__code", flat=True)
            )
            fields = template_fields(product.category, product_type_code(product))
            missing = [
                ProductSpec(
                    product=product,
                    definition=field.spec_definition,
                    value_status=ProductSpec.ValueStatus.UNKNOWN,
                    unit=field.spec_definition.unit,
                )
                for field in fields
                if field.spec_definition.code in applicable_codes
                and field.spec_definition.code not in remaining_codes
            ]
            ProductSpec.objects.bulk_create(missing, ignore_conflicts=True)
            created += len(missing)

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "RECONCILED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: products={products.count()} created={created} "
                f"empty_irrelevant_deleted={deleted} "
                f"extra_values_preserved={preserved_extra_values} "
                f"product_types_reclassified={reclassified}"
            )
        )
