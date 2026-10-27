from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.ruijie.com/vi-vn/products/reyee-switch/ES100-Series-Unmanaged-Switch/RG-ES109G-LP-L/"


VALUES = {
    "dimensions_mm": ("text", "206.5 x 108.5 x 28 mm (W x D x H)", "Dimensions: 206.5 x 108.5 x 28 mm"),
    "fanless": ("boolean", True, "Fanless cooling"),
    "installation": ("text", "Desktop or wall mount", "The switch can be mounted on a table or wall"),
    "mac_address_table": ("text", "8K", "MAC address table: 8000 entries"),
    "max_power_consumption_w": ("number", 64, "Less than 7 W without PoE load; less than 64 W at full PoE load"),
    "operating_temperature_c": ("text", "0 to 45 °C", "Operating temperature: 0°C to 45°C"),
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    if spec.value_boolean is not None:
        return spec.value_boolean
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import manually verified Reyee RG-ES109G-LP-L specs (round 32)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        product = Product.objects.filter(brand=brand, model="RG-ES109G-LP-L", is_published=True).first()
        if not brand or not product:
            raise CommandError("Missing published Reyee RG-ES109G-LP-L")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := set(VALUES) - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Official product page and ES100 datasheet, latest available edition",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "Ruijie Reyee RG-ES100 Unmanaged Switches Datasheet",
                "region": "Vietnam / Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        new = corrected = unchanged = 0
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            new_value = Decimal(str(value)) if kind == "number" else value
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": str(value) if kind == "text" else "",
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": bool(value) if kind == "boolean" else None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the official exact-model product page, datasheet, and hardware installation guide.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Technical specifications and installation sections",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={len(VALUES)} newly_filled={new} corrected={corrected} unchanged={unchanged} models=1"
            )
        )
