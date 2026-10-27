from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


GUIDE_URL = "https://reyee.ruijie.com/en-global/support/documents/slide_R-76393/"

PRODUCTS = {
    "RG-NBS3200-24GT4XS": {
        "section": "1.1.1",
        "values": {
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("1 fixed fan; left-to-rear airflow"),
            "max_power_consumption_w": n(28.028, "28.028 W"),
            "dimensions_mm": t("440 x 207.5 x 43.6 mm"),
        },
    },
    "RG-NBS3200-24SFP/8GT4XS": {
        "section": "1.2.1",
        "values": {
            "mac_address_table": t("16000 entries"),
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("2 fixed fans; left-to-rear airflow"),
            "max_power_consumption_w": n(41.8, "41.8 W"),
            "dimensions_mm": t("440 x 267.5 x 43.6 mm"),
        },
    },
    "RG-NBS3200-24GT4XS-P": {
        "section": "1.3.1",
        "values": {
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("2 fixed fans; left-to-right airflow"),
            "max_power_consumption_w": n(431.86, "431.86 W with full PoE load"),
            "dimensions_mm": t("440 x 357.6 x 43.6 mm"),
        },
    },
    "RG-NBS3200-48GT4XS": {
        "section": "1.4.1",
        "values": {
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("2 fixed fans; side-to-rear airflow"),
            "max_power_consumption_w": n(46.4, "46.4 W"),
            "dimensions_mm": t("440 x 267.5 x 43.6 mm"),
        },
    },
    "RG-NBS3200-48GT4XS-P": {
        "section": "1.5.1",
        "values": {
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("2 fixed fans; side-to-rear airflow"),
            "max_power_consumption_w": n(447.69, "447.69 W with full PoE load"),
            "dimensions_mm": t("440 x 357.6 x 43.6 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee NBS3200 hardware specifications (round 15)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=GUIDE_URL,
            document_version="V1.5, dated 2026-09-30; updated 2026-10-08",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "Ruijie Reyee RG-NBS3200 Series Switches Installation Guide V1.5",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        written = new = corrected = unchanged = 0
        detail = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    old
                    and old.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((old.value_text or "").strip())
                        or old.value_number is not None
                        or old.value_boolean is not None
                    )
                )
                old_value = None if not had else old.value_text if old.value_text else old.value_number
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": GUIDE_URL[:200],
                    "source_note": (
                        "Manually verified from the latest official NBS3200 V1.5 installation guide; "
                        "full-load PoE consumption is used for maximum consumption."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
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
                    source_location=f"Section {row['section']} technical specifications - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            detail.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(detail))
