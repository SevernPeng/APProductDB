from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from catalog.models import Product, ProductSpec, TemplateField
from catalog.product_types import product_type_code
from catalog.services import template_fields
from catalog.spec_applicability import field_is_applicable, specs_by_code


def has_value(spec):
    return bool(
        spec
        and spec.value_status == ProductSpec.ValueStatus.PUBLISHED
        and (
            bool((spec.value_text or "").strip())
            or spec.value_number is not None
            or spec.value_boolean is not None
        )
    )


class Command(BaseCommand):
    help = "Report actual-value coverage for applicable product specification fields."

    def add_arguments(self, parser):
        parser.add_argument("--brand", action="append", dest="brands")
        parser.add_argument("--category", action="append", dest="categories")
        parser.add_argument(
            "--include-optional",
            action="store_true",
            help="Include P1/P2 template fields instead of required P0 fields only.",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Print category and total summaries without the missing-field detail.",
        )

    def handle(self, *args, **options):
        products = Product.objects.filter(is_published=True).select_related(
            "brand", "category", "product_type", "product_model"
        ).prefetch_related(
            Prefetch(
                "specs",
                queryset=ProductSpec.objects.select_related("definition").prefetch_related(
                    "evidence"
                ),
            )
        )
        if options["brands"]:
            products = products.filter(brand__name__in=options["brands"])
        if options["categories"]:
            products = products.filter(category__slug__in=options["categories"])

        totals = defaultdict(lambda: [0, 0])
        fields_total = defaultdict(lambda: [0, 0, []])
        products_with_actual = 0
        products_with_applicable_fields = 0
        for product in products:
            current = specs_by_code(product)
            products_with_actual += int(any(has_value(spec) for spec in current.values()))
            fields = template_fields(product.category, product_type_code(product))
            if not options["include_optional"]:
                fields = [
                    field
                    for field in fields
                    if field.priority == TemplateField.Priority.P0 and field.required
                ]
            applicable_for_product = 0
            for field in fields:
                code = field.spec_definition.code
                if not field_is_applicable(product, code, current):
                    continue
                applicable_for_product += 1
                totals[product.category.slug][0] += 1
                totals[product.category.slug][1] += int(has_value(current.get(code)))
                fields_total[(product.category.slug, code)][0] += 1
                fields_total[(product.category.slug, code)][1] += int(
                    has_value(current.get(code))
                )
                if not has_value(current.get(code)):
                    fields_total[(product.category.slug, code)][2].append(
                        f"{product.brand.name} {product.model}"
                    )
            products_with_applicable_fields += int(applicable_for_product > 0)

        total = sum(item[0] for item in totals.values())
        populated = sum(item[1] for item in totals.values())
        for category, (category_total, category_populated) in sorted(totals.items()):
            percent = category_populated / category_total * 100 if category_total else 0
            self.stdout.write(
                f"{category}: {category_populated}/{category_total} ({percent:.2f}%)"
            )
        percent = populated / total * 100 if total else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"TOTAL: {populated}/{total} ({percent:.2f}%) products={products.count()}"
            )
        )
        product_count = products.count()
        product_percent = products_with_actual / product_count * 100 if product_count else 0
        self.stdout.write(
            f"PRODUCTS WITH ANY ACTUAL SPEC: {products_with_actual}/{product_count} "
            f"({product_percent:.2f}%); products_with_applicable_fields={products_with_applicable_fields}"
        )
        if options["summary_only"]:
            return
        self.stdout.write("MISSING BY FIELD:")
        for (category, code), (field_total, field_populated, missing_products) in sorted(
            fields_total.items(),
            key=lambda item: (
                -(item[1][0] - item[1][1]),
                item[0][0],
                item[0][1],
            ),
        ):
            missing = field_total - field_populated
            if missing:
                self.stdout.write(
                    f"{category}.{code}: missing={missing} "
                    f"coverage={field_populated / field_total * 100:.2f}% "
                    f"({field_populated}/{field_total}) "
                    f"models={'; '.join(missing_products[:12])}"
                )
