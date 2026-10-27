from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MODEL = "RG-RAP62-OD"
URL = "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/10/RG-RAP62-OD_Datasheet_Official_2026-05-10.pdf"
VALUES = {
    "antenna_gain_dbi": (
        "2.4 GHz: 4.00 dBi; 5 GHz: 6.50 dBi",
        "Antenna gain (2.4 GHz): 4.00 dBi; Antenna gain (5 GHz): 6.50 dBi",
        "Hardware Specifications - Antenna",
    ),
    "wireless_range": (
        "Recommended: 50 m at 2.4 GHz, 150 m at 5 GHz; maximum: 100 m at 2.4 GHz, 300 m at 5 GHz (ideal unobstructed environment)",
        "Coverage range: 5 GHz max 300 m; 2.4 GHz max 100 m; 5 GHz recommended 150 m; 2.4 GHz recommended 50 m. Data obtained in an ideal environment without obstruction.",
        "Hardware Specifications - Wi-Fi Radio - Coverage range",
    ),
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import exact RG-RAP62-OD antenna gain and coverage range (round 56)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        product = Product.objects.filter(
            brand=brand, model=MODEL, is_published=True
        ).first()
        definitions = {
            definition.code: definition
            for definition in SpecDefinition.objects.filter(code__in=VALUES)
        }
        if not brand or not product or set(definitions) != set(VALUES):
            raise CommandError("Missing Reyee product or required AP definitions")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Official Datasheet 2026-05-10",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "RG-RAP62-OD Datasheet Official",
                "region": "Global",
                "published_date": date(2026, 5, 10),
                "accessed_date": accessed,
                "active": True,
            },
        )

        new = corrected = unchanged = 0
        details = []
        for code, (value, raw, location) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(
                product=product, definition=definition
            ).first()
            old_value = actual(old)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value,
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": value,
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the latest official exact-model Reyee datasheet.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != value:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location=location,
                defaults={
                    "source_excerpt": raw,
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            details.append(f"{code}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={len(VALUES)} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} models=1"
            )
        )
        self.stdout.write("; ".join(details))
