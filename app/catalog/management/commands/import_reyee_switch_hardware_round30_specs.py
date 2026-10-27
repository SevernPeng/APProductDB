from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


NBS3200_GUIDE = "https://reyee.ruijie.com/en-global/support/documents/slide_R-76393/"
NBS3300_GUIDE = (
    "https://reyee.ruijie.com/en-global/support/documents/"
    "slide_rg-nbs3300-8mg2xs-p-rg-nbs3300-16mg4xs-p-switches-installation-guide/"
)
NIS2100_GUIDE = (
    "https://reyee.ruijie.com/en-global/support/documents/"
    "slide_rg-nis2100-series-switches-implementation-cookbook/"
)


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


PRODUCTS = {
    "RG-NBS3200-24SFP": {
        "url": NBS3200_GUIDE,
        "title": "RG-NBS3200 Series Switches Installation Guide V1.5",
        "version": "V1.5, 2026-09-30",
        "location": "Section 1.2.1 Technical Specifications",
        "values": {
            "ethernet_interfaces": t(
                "24 x 1GE SFP ports (8 combo 10/100/1000BASE-T); 4 x 10GE SFP+ ports"
            ),
            "flash_memory": t("V1/V2 hardware: 256 MB; V3 hardware: 128 MB"),
            "dimensions_mm": t("440 x 267.5 x 43.6 mm (W x D x H)"),
            "fan_design": t("2 x fixed fans"),
            "max_power_consumption_w": n(41.8, "Maximum power consumption: 41.8 W"),
            "power_supply": t(
                "Fixed AC power supply, 100-240 V, 50/60 Hz, maximum input current 2 A",
                "Fixed power supply; rated input 100-240 V AC, 50/60 Hz; maximum input 90-264 V AC, 47-63 Hz; maximum input current 2 A",
            ),
        },
        "clear": {
            "poe_budget_w": "This is the non-PoE RG-NBS3200-24SFP/8GT4XS; the V1.5 port table lists no PoE ports."
        },
    },
    "RG-NBS3300-8MG2XS-P": {
        "url": NBS3300_GUIDE,
        "title": "RG-NBS3300-8MG2XS-P Switch Installation Guide and Exact-Model Datasheet",
        "version": "Latest official guide page updated 2026-01-22; exact-model datasheet 2025-11",
        "location": "Technical specifications / hardware specifications",
        "values": {
            "dimensions_mm": t("300 x 233 x 43.6 mm (W x D x H)"),
            "fan_design": t("2 x fixed fans; left-to-right airflow"),
            "max_power_consumption_w": n(
                278, "27 W with no PoE load; 278 W with full PoE load"
            ),
            "power_supply": t(
                "Single fixed AC power supply, 100-240 V, 50/60 Hz, maximum input current 4.5 A",
                "Fixed power supply; rated input 100-240 V AC, 50/60 Hz; maximum input 90-264 V AC, 47-63 Hz; maximum input current 4.5 A",
            ),
        },
        "clear": {},
    },
    "RG-NIS2100-4GT2SFP-HP": {
        "url": NIS2100_GUIDE,
        "title": "Ruijie Reyee RG-NIS2100 Series Switches Implementation Cookbook V1.1",
        "version": "V1.1, updated 2025-08-18; exact-model datasheet 2025-10-24",
        "location": "Installation Guide technical specifications / exact-model datasheet hardware specifications",
        "values": {
            "flash_memory": t("8 MB"),
            "dimensions_mm": t("50 x 155 x 130 mm (W x D x H)"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(
                192, "12 W with no PoE load; 192 W with full PoE load"
            ),
            "power_supply": t(
                "46-57 V DC input, 4.2 A; external DC adapter or RG-NIS power module (not included)"
            ),
        },
        "clear": {},
    },
    "RG-NIS2100-8GT2SFP-HP": {
        "url": NIS2100_GUIDE,
        "title": "Ruijie Reyee RG-NIS2100 Series Switches Implementation Cookbook V1.1",
        "version": "V1.1, updated 2025-08-18; exact-model datasheet 2025-10-24",
        "location": "Installation Guide technical specifications / exact-model datasheet hardware specifications",
        "values": {
            "flash_memory": t("8 MB"),
            "dimensions_mm": t("50 x 155 x 130 mm (W x D x H)"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(
                312, "12 W with no PoE load; 312 W with full PoE load"
            ),
            "power_supply": t(
                "46-57 V DC input, 7 A; external DC adapter or RG-NIS power module (not included)"
            ),
        },
        "clear": {},
    },
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
    help = "Import manually verified Reyee switch hardware specs (round 30)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in set(row["values"]) | set(row["clear"])}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = cleared = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.SUPPORT,
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = model_cleared = 0
            for code, note in row["clear"].items():
                spec = ProductSpec.objects.filter(product=product, definition=definitions[code]).first()
                if actual(spec) is None:
                    continue
                spec.evidence.all().delete()
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""
                spec.value_number = None
                spec.value_boolean = None
                spec.normalized_value = ""
                spec.raw_value = ""
                spec.source_url = ""
                spec.source_note = f"Manual source audit: {note}"
                spec.verified_date = accessed
                spec.save()
                cleared += 1
                model_cleared += 1

            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value)) if kind == "number" else str(value)
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "" if kind == "number" else str(value),
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": (
                        "Manually verified from the newest available official exact-series installation guide "
                        "and exact-model datasheet; full-PoE-load maximum is used where applicable."
                    ),
                    "verified_date": accessed,
                }
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
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
                    source_location=row["location"],
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(
                f"{model}:+{model_new}/corrected:{model_corrected}/cleared:{model_cleared}"
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} cleared={cleared} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(details))
