from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP72Pro": {
        "url": "https://reyee.ruijie.com/it-it/support/documents/slide_rg-rap72pro-access-point-installation-guide-it/",
        "version": "RG-RAP72Pro Installation Guide V1.2",
        "value": "2.4 GHz: 3.0 dBi; 5 GHz: 4.0 dBi",
        "raw": "PIFA antenna gain: 2.4 GHz 3.0 dBi; 5 GHz 4.0 dBi",
    },
    "RG-RAP73Pro": {
        "url": "https://reyee.ruijie.com/fr-fr/support/documents/slide_ruijie-rg-rap73pro-installation-guide-fr/",
        "version": "RG-RAP73Pro Installation Guide V1.0, 2026-02-12",
        "value": "2.4 GHz: 3.6 dBi; 5 GHz: 5.9 dBi; 6 GHz: 5.2 dBi",
        "raw": "Built-in omnidirectional antenna gain: 2.4 GHz 3.6 dBi; 5 GHz 5.9 dBi; 6 GHz 5.2 dBi",
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import exact-model Reyee Wi-Fi 7 AP antenna gains from official installation guides (round 41)."

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
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"], document_version=row["version"],
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.SUPPORT,
                    "title": f"{model} Official Installation Guide",
                    "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": row["value"], "value_number": None, "value_boolean": None,
                    "normalized_value": row["value"], "unit": definition.unit,
                    "raw_value": row["raw"], "source_url": row["url"][:200],
                    "source_note": "Manually verified from the newest available official exact-model installation guide.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
            elif old_value != row["value"]:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=source,
                source_location="Technical specifications / antenna table",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {row['raw']}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
