from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


GUIDE_URL = "https://www.ruijie.com/en-global/support/documents/slide_76392/"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


PRODUCTS = {
    "RG-NBS3100-24GT4SFP": {
        "url": GUIDE_URL,
        "title": "RG-NBS3100 Series Switches Installation Guide V1.3",
        "document_type": SourceDocument.DocumentType.SUPPORT,
        "location": "Section 1.1.1 Technical Specifications",
        "values": {
            "dimensions_mm": t("440 x 165 x 44 mm (W x D x H)"),
            "fan_design": t("Fanless", "Number of fans: Fanless; natural heat dissipation"),
            "max_power_consumption_w": n(21, "Power consumption: 21 W"),
            "power_supply": t(
                "AC input, 100-240 V, 50/60 Hz, 0.6 A",
                "AC input; rated voltage 100-240 V; 50/60 Hz; rated current 0.6 A",
            ),
        },
        "clear": {
            "poe_budget_w": "The official installation guide explicitly states that PoE is not supported."
        },
    },
    "RG-NBS3100-24GT4SFP-P": {
        "url": GUIDE_URL,
        "title": "RG-NBS3100 Series Switches Installation Guide V1.3",
        "document_type": SourceDocument.DocumentType.SUPPORT,
        "location": "Section 1.2.1 Technical Specifications",
        "values": {
            "dimensions_mm": t("440 x 293 x 44 mm (W x D x H)"),
            "fan_design": t("2 fans", "Number of fans: Two fans"),
            "max_power_consumption_w": n(443, "21 W with no PoE load; 443 W with PoE full load"),
            "power_supply": t(
                "AC input, 100-240 V, 50/60 Hz, 6 A",
                "AC input; rated voltage 100-240 V; 50/60 Hz; rated current 6 A",
            ),
        },
        "clear": {},
    },
    "RG-NBS3100-8GT2SFP": {
        "url": GUIDE_URL,
        "title": "RG-NBS3100 Series Switches Installation Guide V1.3",
        "document_type": SourceDocument.DocumentType.SUPPORT,
        "location": "Section 1.3.1 Technical Specifications",
        "values": {
            "dimensions_mm": t("260 x 120 x 43.6 mm (W x D x H)"),
            "fan_design": t("Fanless", "Number of fans: Fanless; natural heat dissipation"),
            "max_power_consumption_w": n(8, "Power consumption: 8 W"),
            "power_supply": t(
                "External adapter, 100-240 V AC input, 12 V DC / 1 A output",
                "Adapter input: 100-240 V AC, 50/60 Hz, 1 A; output: 12 V DC, 1 A",
            ),
        },
        "clear": {
            "poe_budget_w": "The official installation guide explicitly states that PoE is not supported."
        },
    },
    "RG-NBS3100-8GT2SFP-P": {
        "url": GUIDE_URL,
        "title": "RG-NBS3100 Series Switches Installation Guide V1.3",
        "document_type": SourceDocument.DocumentType.SUPPORT,
        "location": "Section 1.4.1 Technical Specifications",
        "values": {
            "dimensions_mm": t("300 x 220 x 43.6 mm (W x D x H)"),
            "fan_design": t("Fanless", "Number of fans: Fanless; natural heat dissipation"),
            "max_power_consumption_w": n(145, "11 W with no PoE load; 145 W with PoE full load"),
            "power_supply": t(
                "AC input, 100-240 V, 50/60 Hz, 2 A",
                "AC input; rated voltage 100-240 V; 50/60 Hz; rated current 2 A",
            ),
        },
        "clear": {},
    },
    "RG-NBS3100-48GT4SFP-P": {
        "url": "https://reyee.ruijie.com/en-global/resources/preview/rg-nbs3100-48gt4sfp-p-datasheet/",
        "title": "RG-NBS3100-48GT4SFP-P Datasheet Official",
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "location": "Physical Features table",
        "values": {
            "fan_design": t("2 fans", "Fan: 2; adaptive speed adjustment"),
            "max_power_consumption_w": n(447.69, "Maximum power consumption: 447.69 W"),
            "power_supply": t(
                "Fixed AC power supply, 100-240 V, 50/60 Hz, 7 A",
                "Fixed power supply; 100-240 V AC; rated current 7 A",
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
    help = "Import manually verified Reyee NBS3100 switch hardware specs (round 29)."

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
                document_version="Official guide/datasheet, latest exact-model edition available",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": row["document_type"],
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
                        "Manually verified from the official exact-model installation guide or datasheet; "
                        "maximum power uses the full-PoE-load figure where applicable."
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
