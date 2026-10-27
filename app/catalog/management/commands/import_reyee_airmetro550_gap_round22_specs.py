from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL = "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/airmetro-series/airmetro550g-b/"
VALUES = {
    "max_channel_width_mhz": (
        "number", 80, "2.4 GHz channel width: Auto/20/40 MHz; 5 GHz: Auto/20/40/80 MHz"
    ),
    "centralized_management": (
        "text", "Ruijie Cloud; Ruijie Reyee App",
        "All-in-one cloud management; restarting through Ruijie Reyee App: Yes",
    ),
    "antenna_type": (
        "text", "External antenna; compatible with RG-ANT13-360, RG-ANT16S-120, RG-ANT20S-90",
        "Performance tables specify the attached RG-ANT13-360, RG-ANT16S-120, or RG-ANT20S-90 antenna",
    ),
}


class Command(BaseCommand):
    help = "Import/correct manually verified Reyee RG-AirMetro550G-B product-page specs (round 22)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        product = Product.objects.filter(brand=brand, model="RG-AirMetro550G-B", is_published=True).first()
        if not product:
            raise CommandError("Missing published Reyee product: RG-AirMetro550G-B")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Current official global product page, accessed 2026-10-21",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "RG-AirMetro550G-B official product page",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        written = new = corrected = unchanged = 0
        for code, (kind, value, raw) in VALUES.items():
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
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the current official Reyee product page.",
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
                source_document=source,
                source_location="Highlight Features / Key Specifications / Applications",
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
