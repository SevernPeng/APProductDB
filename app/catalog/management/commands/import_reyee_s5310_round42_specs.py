from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.ruijie.com/en-global/products/switches/campus-switches/rg-s5310-48sfp4xs-e"

PRODUCTS = {
    "RG-S5310-24GT4XS-E": (115, 154, "RG-S5310-24GT4XS-E"),
    "RG-S5310-24GT4XS-P-E": (115, 154, "RG-S5310-24GT4XS-P-E"),
    "RG-S5310-48GT4XS-E": (158, 211, "RG-S5310-48GT4XS-E"),
    # The catalog spelling omits the hyphen before P; the official family table uses the canonical name below.
    "RG-S5310-48GT4XSP-E": (158, 211, "RG-S5310-48GT4XS-P-E"),
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_number


class Command(BaseCommand):
    help = "Import Ruijie S5310-E forwarding and switching capacities from the official family table (round 42)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {d.code: d for d in SpecDefinition.objects.filter(
            code__in=["packet_forwarding_rate_mpps", "switching_capacity_gbps"]
        )}
        if not brand or len(definitions) != 2:
            raise CommandError("Missing Reyee brand or switch-capacity definitions")
        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, (forwarding, switching, official_model) in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=SOURCE_URL, document_version=f"Current official S5310-E family table: {official_model}",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"{official_model} Official S5310-E Product Family Specifications",
                    "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            values = {
                "packet_forwarding_rate_mpps": (forwarding, f"System packet forwarding rate: {forwarding} Mpps"),
                "switching_capacity_gbps": (switching, f"System switching capacity: {switching} Gbps"),
            }
            model_new = model_corrected = 0
            for code, (value, raw) in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value))
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "", "value_number": new_value, "value_boolean": None,
                        "normalized_value": str(value), "unit": definition.unit,
                        "raw_value": raw, "source_url": SOURCE_URL[:200],
                        "source_note": f"Manually verified from the official S5310-E family table under canonical model {official_model}.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"System Specifications table, {official_model} column",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
