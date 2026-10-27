from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = (
    "https://reyee.ruijie.com/en-global/support/documents/"
    "slide_rg-es2-nis2100-series-switches-1-0-1-b1p58-configuration-guide/"
)

MODELS = [
    "RG-ES206GS-P",
    "RG-ES206MG-P",
    "RG-ES209MG-P",
    "RG-ES210GS-P",
    "RG-ES220GS-P",
    "RG-ES228GS-LP",
    "RG-ES228GS-P",
    "RG-NIS2100-4GT2SFP-HP",
    "RG-NIS2100-8GT2SFP-HP",
]


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import official RG-ES2/NIS2100 loop-prevention support (round 44)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definition = SpecDefinition.objects.filter(code="stp_features").first()
        if not brand or not definition:
            raise CommandError("Missing Reyee brand or stp_features definition")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        value = "Loop prevention supported"
        raw = (
            "Loop Prevention is supported by switch models suffixed with -P, -LP, -HP, or -UP "
            "in the Supported Hardware Models list."
        )
        for model in MODELS:
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=SOURCE_URL,
                document_version=f"V1.0, RG-ES2/NIS2100 loop-prevention applicability: {model}",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.SUPPORT,
                    "title": "Ruijie Reyee RG-ES2 and NIS2100 Series Switches Configuration Guide",
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
                    "source_note": (
                        "Manually verified from the official current RG-ES2/NIS2100 configuration guide; "
                        "the model suffix is explicitly covered by the guide's applicability rule."
                    ),
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
                source_location="Monitoring > Loop Prevention; Supported Hardware Models",
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
            f"unchanged={unchanged} models={len(MODELS)}"
        ))
        self.stdout.write("; ".join(details))
