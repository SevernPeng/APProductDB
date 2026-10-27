from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCT_URL = "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est350v2/"
COOKBOOK_URL = "https://reyee.ruijie.com/en-global/support/documents/slide_77313/?page=html"

VALUES = {
    "dimensions_mm": ("text", "132 x 48 x 230 mm (W x D x H), excluding mounting bracket", PRODUCT_URL,
                      "Product dimensions: 132 mm x 48 mm x 230 mm (excluding mounting bracket)"),
    "beamwidth": ("text", "Horizontal 31°; vertical 14°", PRODUCT_URL,
                  "Antenna horizontal orientation: 31°; vertical orientation: 14°"),
    "max_channel_width_mhz": ("number", 80, PRODUCT_URL, "5 GHz channel width: Auto/20/40/80 MHz"),
    "supported_bands": ("text", "5 GHz", PRODUCT_URL,
                        "Single-radio; Radio 1: 5 GHz, 2 spatial streams, 2 x 2 MIMO"),
    "centralized_management": ("text", "Ruijie Cloud; Ruijie Reyee App", PRODUCT_URL,
                               "Ruijie Cloud remote monitoring; restarting through Ruijie Reyee App: Yes"),
    "antenna_type": ("text", "Built-in directional antenna", COOKBOOK_URL,
                     "Device Specification: Antenna Type - Built-in Directional Antenna"),
}


class Command(BaseCommand):
    help = "Import and correct manually verified Reyee RG-EST350 V2 specifications (round 20)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        product = Product.objects.filter(brand=brand, model="RG-EST350", is_published=True).first()
        if not product:
            raise CommandError("Missing published Reyee product: RG-EST350")

        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        sources = {}
        sources[PRODUCT_URL], _ = SourceDocument.objects.update_or_create(
            url=PRODUCT_URL,
            document_version="Current RG-EST350 V2 official global product page, accessed 2026-10-21",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "RG-EST350 V2 official product page",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        sources[COOKBOOK_URL], _ = SourceDocument.objects.update_or_create(
            url=COOKBOOK_URL,
            document_version="V1.5, updated 2024-03-28",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "Ruijie Reyee RG-EST, AirMetro Series Wireless Bridges Implementation Cookbook",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        written = new = corrected = unchanged = 0
        for code, (kind, value, url, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((old.value_text or "").strip()) or old.value_number is not None
                or old.value_boolean is not None
            ))
            old_value = None if not had else (old.value_number if kind == "number" else old.value_text)
            new_value = Decimal(str(value)) if kind == "number" else str(value)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "" if kind == "number" else str(value),
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": url[:200],
                    "source_note": "Manually verified from the official current-version product page/support document.",
                    "verified_date": accessed,
                },
            )
            if not had:
                new += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=sources[url],
                source_location="RG-EST350 V2 Key Specifications / Device Specification",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models=1"
        ))
