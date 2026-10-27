from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://reyee.ruijie.com/tr-tr/products/reyee-switch/es224gc/"

PRODUCTS = {
    "RG-ES205GC": {"stp_features": "Automatic loop prevention", "vlan_count": 16},
    "RG-ES205GC-P": {
        "stp_features": "Automatic loop prevention",
        "vlan_count": 16,
        "dimensions_mm": "148 x 78 x 26 mm",
    },
    "RG-ES206GC-P": {"stp_features": "Automatic loop prevention"},
    "RG-ES208GC": {"stp_features": "Automatic loop prevention", "vlan_count": 16},
    "RG-ES209GC-P": {"stp_features": "Automatic loop prevention"},
    "RG-ES216GC": {"stp_features": "Automatic loop prevention", "vlan_count": 16},
    "RG-ES218GC-P": {"stp_features": "Automatic loop prevention"},
    "RG-ES224GC": {"stp_features": "Automatic loop prevention", "vlan_count": 16},
    "RG-ES226GC-P": {
        "stp_features": "Automatic loop prevention",
        "vlan_count": 16,
        "mac_address_table": "8K",
    },
}


RAW_VALUES = {
    "stp_features": "Loop prevention: Supported (automatic loop prevention)",
    "vlan_count": "VLAN: 16",
    "dimensions_mm": "Dimensions (W x D x H): 148 mm x 78 mm x 26 mm",
    "mac_address_table": "MAC address table: 8000 entries",
}


def actual(spec, data_type):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if data_type in {"integer", "decimal"}:
        return spec.value_number
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import manually verified Reyee ES200 comparison-table gaps (round 43)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if not brand or len(definitions) != len(codes):
            raise CommandError("Missing Reyee brand or ES200 specification definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=SOURCE_URL,
                document_version=f"Current official ES200 family comparison table: {model}",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"{model} Official ES200 Family Comparison",
                    "region": "Turkey",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, value in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old, definition.data_type)
                is_number = definition.data_type in {"integer", "decimal"}
                new_value = Decimal(str(value)) if is_number else value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if is_number else value,
                        "value_number": new_value if is_number else None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": definition.unit,
                        "raw_value": RAW_VALUES[code],
                        "source_url": SOURCE_URL[:200],
                        "source_note": "Manually verified from the current official Reyee ES200 family comparison table.",
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
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Comparison table, {model} column",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {RAW_VALUES[code]}",
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
