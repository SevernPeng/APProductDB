from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


SOURCE = "https://www.dlink.com/-/media/Business_Products/DGS/DGS%203620/Manual/DGS3620_Series_HW_Installation_Guide_v250.pdf"


BASE_VALUES = {
    "DGS-3620-28TC": ("441 x 310 x 44 mm", 45.1),
    "DGS-3620-28PC": ("441 x 380 x 44 mm", 502.2),
    "DGS-3620-52T": ("441 x 380 x 44 mm", 76.0),
    "DGS-3620-52P": ("441 x 380 x 44 mm", 517.1),
}


PRODUCTS = {}
for base_model, (dimensions, power) in BASE_VALUES.items():
    for model in (base_model, f"{base_model}/EI"):
        PRODUCTS[model] = {
            "location": f"Hardware version B1 physical/environmental table - {base_model}",
            "values": {
                "dimensions_mm": t(dimensions),
                "max_power_consumption_w": n(power, f"{power} W maximum for hardware version B1"),
                "operating_temperature_c": t("0 to 50 °C"),
            },
        }


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-3620 physical specifications (round 10)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE,
            document_version="Hardware installation guide v2.50; newest B1 values; accessed 2026-10-14",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "D-Link DGS-3620 Series Hardware Installation Guide v2.50",
                "region": "Worldwide",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": SOURCE[:200],
                    "source_note": (
                        "Manually verified from the official hardware guide. Newer B1 figures were selected; "
                        "SI and EI software licenses share identical hardware."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
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
                    source_location=f"{row['location']} - {model}",
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
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
