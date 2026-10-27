from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch

from catalog.models import Product, ProductSpec
from catalog.product_types import infer_switch_management_type
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
    help = "Audit switch taxonomy and conditional field applicability."

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-issues", action="store_true")

    def handle(self, *args, **options):
        products = Product.objects.filter(
            category__slug__in={
                "managed-switches",
                "unmanaged-easy-smart-switches",
            }
        ).select_related(
            "brand", "category", "product_type", "product_model"
        ).prefetch_related(
            Prefetch(
                "specs",
                queryset=ProductSpec.objects.select_related("definition").prefetch_related(
                    "evidence"
                ),
            )
        )
        issues = defaultdict(list)
        for product in products:
            current = specs_by_code(product)
            current_type = product.product_type.code if product.product_type_id else ""
            if product.category.slug == "unmanaged-easy-smart-switches":
                management = current.get("management_type")
                management_value = (
                    management.value_text
                    if has_published_value(management)
                    else ""
                )
                expected_type = infer_switch_management_type(
                    management_value,
                    switch_has_management_features(current),
                )
                if expected_type and not current_type.startswith(f"{expected_type}_"):
                    issues["management_type_mismatch"].append(product)
                if field_is_applicable(product, "management_methods", current):
                    issues["duplicate_management_field"].append(product)

            poe_state = switch_poe_state(product, current)
            applicable_poe = {
                code
                for code in POE_OUTPUT_SPEC_CODES
                if field_is_applicable(product, code, current)
            }
            if poe_state is not True and applicable_poe:
                issues["unconfirmed_poe_fields_applicable"].append(product)

            template_codes = {
                field.spec_definition.code
                for field in template_fields(
                    product.category,
                    current_type,
                )
            }
            if (
                product.category.slug == "unmanaged-easy-smart-switches"
                and "management_methods" in template_codes
            ):
                issues["duplicate_management_template"].append(product)

        issue_count = sum(len(items) for items in issues.values())
        self.stdout.write(f"SWITCHES AUDITED: {products.count()}")
        if not issues:
            self.stdout.write(self.style.SUCCESS("SWITCH CONSISTENCY: PASS"))
            return
        for code, items in sorted(issues.items()):
            examples = "; ".join(
                f"{item.brand.name} {item.model}" for item in items[:12]
            )
            self.stdout.write(f"{code}: {len(items)} ({examples})")
        message = f"SWITCH CONSISTENCY: FAIL ({issue_count} issue instances)"
        if options["fail_on_issues"]:
            raise CommandError(message)
        self.stdout.write(self.style.ERROR(message))
