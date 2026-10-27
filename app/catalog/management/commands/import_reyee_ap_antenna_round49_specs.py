from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP62": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/3/11/RG-RAP62_Datasheet_Official_2026-03-11.pdf",
        "value": "2.4 GHz: 3.13 dBi; 5 GHz: 4.58 dBi",
        "raw": "Antenna gain (2.4 GHz): 3.13 dBi; Antenna gain (5 GHz): 4.58 dBi",
    },
    "RG-RAP2260": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/3/11/RG-RAP2260_Datasheet_Official_2026-03-11.pdf",
        "value": "2.4 GHz: 3.00 dBi; 5 GHz: 3.00 dBi",
        "raw": "Antenna gain (2.4 GHz): 3.00 dBi; Antenna gain (5 GHz): 3.00 dBi",
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import exact antenna-gain gaps from official 2026 Reyee AP datasheets (round 49)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definition = SpecDefinition.objects.filter(code="antenna_gain_dbi").first()
        if not brand or not definition:
            raise CommandError("Missing Reyee brand or antenna_gain_dbi definition")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Official Datasheet 2026-03-11",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Ruijie Reyee {model} Official Datasheet",
                    "region": "Global",
                    "published_date": date(2026, 3, 11),
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": row["value"],
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": row["value"],
                    "unit": definition.unit,
                    "raw_value": row["raw"],
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the latest official exact-model datasheet dated 2026-03-11.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != row["value"]:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Hardware Specifications - Antenna",
                defaults={
                    "source_excerpt": row["raw"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{model}.antenna_gain_dbi:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
