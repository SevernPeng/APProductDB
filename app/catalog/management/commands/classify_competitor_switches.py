from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, ProductType
from catalog.product_types import infer_managed_switch_poe, infer_product_type_code
from catalog.spec_applicability import (
    has_published_value,
    specs_by_code,
    switch_poe_state,
)


class Command(BaseCommand):
    help = "Classify unknown competitor managed switches without changing specifications."

    def add_arguments(self, parser):
        parser.add_argument("--brand", action="append", dest="brands")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        products = (
            Product.objects.filter(
                is_published=True,
                category__slug="managed-switches",
                product_type__code="unknown",
            )
            .exclude(brand__is_own_brand=True)
            .select_related("brand", "category", "product_type", "product_model")
            .prefetch_related("specs__definition", "specs__evidence")
            .order_by("brand__name", "model")
        )
        if options["brands"]:
            products = products.filter(brand__name__in=options["brands"])

        type_ids = {
            product_type.code: product_type.id
            for product_type in ProductType.objects.filter(
                category__slug="managed-switches", active=True
            )
        }
        changed = Counter()
        unresolved = Counter()
        for product in products:
            current = specs_by_code(product)
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
            model_poe = infer_managed_switch_poe(
                product.brand.name,
                product.model,
                getattr(product.product_model, "product_name", ""),
            )
            inferred = infer_product_type_code(
                "managed-switches",
                product.model,
                has_poe=(
                    model_poe
                    if model_poe is not None
                    else switch_poe_state(product, current)
                ),
                product_name=getattr(product.product_model, "product_name", ""),
                brand_name=product.brand.name,
                feature_text=feature_text,
            )
            if inferred in {"", "unknown"}:
                unresolved[product.brand.name] += 1
                continue
            product.product_type_id = type_ids[inferred]
            product.save(update_fields=("product_type", "updated_at"))
            changed[(product.brand.name, inferred)] += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "CLASSIFIED"
        self.stdout.write(f"{mode}: changed={sum(changed.values())} unresolved={sum(unresolved.values())}")
        for (brand, product_type), count in sorted(changed.items()):
            self.stdout.write(f"  {brand}: {product_type}={count}")
        if unresolved:
            self.stdout.write("Unresolved:")
            for brand, count in sorted(unresolved.items()):
                self.stdout.write(f"  {brand}: {count}")
