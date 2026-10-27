from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = (
    "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/1/12/"
    "Reyee%20Passive%20PoE%20Adapter%20Series-20260112.pdf"
)

PRODUCTS = {
    "RG-POE-AF15": ("92 x 46.5 x 29.5 mm", "Dimensions: 92 x 46.5 x 29.5 ± 1 mm"),
    "RG-POE-AT30": ("95.2 x 52.2 x 33.2 mm", "Dimensions: 95.2 x 52.2 x 33.2 ± 1 mm"),
    "RG-POE-50-60W-MG": ("137.4 x 62.3 x 32.6 mm", "Dimensions: 137.4 x 62.3 x 32.6 mm"),
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import official Reyee passive PoE adapter dimensions (round 45)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definition = SpecDefinition.objects.filter(code="dimensions_mm").first()
        if not brand or not definition:
            raise CommandError("Missing Reyee brand or dimensions_mm definition")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, (value, raw) in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=SOURCE_URL,
                document_version=f"Official series datasheet dated 2026-01-12: {model}",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Reyee Passive PoE Adapter Series Datasheet - {model}",
                    "region": "Global",
                    "published_date": None,
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
                    "value_text": value,
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": value,
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the official January 2026 passive PoE adapter series datasheet.",
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
                source_location=f"Specifications table, {model} column, page 5",
                defaults={
                    "source_excerpt": raw,
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{model}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
