from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Product, ProductSpec, SpecDefinition


STANDARD_BANDS = {
    "wi-fi 6": "2.4 GHz / 5 GHz",
    "wifi 6": "2.4 GHz / 5 GHz",
    "wi-fi 6e": "2.4 GHz / 5 GHz / 6 GHz",
    "wifi 6e": "2.4 GHz / 5 GHz / 6 GHz",
    "wi-fi 7": "2.4 GHz / 5 GHz / 6 GHz",
    "wifi 7": "2.4 GHz / 5 GHz / 6 GHz",
}


def bands_for_standard(wifi_standard):
    return STANDARD_BANDS.get(" ".join((wifi_standard or "").strip().casefold().split()))


class Command(BaseCommand):
    help = "Fill missing AP supported-band values from Wi-Fi generation without replacing published values."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--brand")
        parser.add_argument("--model")

    def handle(self, *args, **options):
        definition = SpecDefinition.objects.get(code="supported_bands")
        products = Product.objects.filter(
            category__slug="access-point",
            is_published=True,
        ).select_related("brand")
        if options["brand"]:
            products = products.filter(brand__name=options["brand"])
        if options["model"]:
            products = products.filter(model=options["model"])

        candidates = []
        for product in products.order_by("brand__name", "model"):
            inferred = bands_for_standard(product.wifi_standard)
            if not inferred:
                continue
            current = ProductSpec.objects.filter(
                product=product,
                definition=definition,
                value_status=ProductSpec.ValueStatus.PUBLISHED,
            ).first()
            if current:
                continue
            candidates.append((product, inferred))

        self.stdout.write(
            f"Mode: {'apply' if options['apply'] else 'dry-run'}; candidates: {len(candidates)}"
        )
        for product, inferred in candidates:
            self.stdout.write(f"{product.brand.name} {product.model}: {product.wifi_standard} -> {inferred}")

        if not options["apply"]:
            return

        with transaction.atomic():
            for product, inferred in candidates:
                ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": inferred,
                        "value_number": None,
                        "value_boolean": None,
                        "normalized_value": inferred,
                        "unit": "",
                        "raw_value": f"Inferred from declared Wi-Fi generation: {product.wifi_standard}",
                        "source_url": product.official_url,
                        "source_note": (
                            "Derived fallback from the declared Wi-Fi generation; official product-specific "
                            "radio-band specifications take precedence and are never overwritten."
                        ),
                        "verified_date": timezone.localdate(),
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"Applied {len(candidates)} inferred supported-band values."))
