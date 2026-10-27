from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


SOURCES = {
    "poe_gen1": "https://dl.ui.com/datasheets/unifi/UniFi_PoE_Switch.pdf",
    "poe_gen2": "https://dl.ui.com/ds/usw_poe_ds.pdf",
    "usw24": "https://dl.ui.com/ds/usw-24_ds.pdf",
    "usw48": "https://dl.ui.com/ds/usw-48_ds.pdf",
    "pro": "https://dl.ui.com/ds/usw-pro-ds.pdf",
    "aggregation": "https://dl.ui.com/ds/usw-aggregation-ds.pdf",
}

MODELS = {
    "US-8-150W": {
        "source": "poe_gen1",
        "values": {
            "fan_design": t("Fanless", "Sound level: 0.5 dBr (fanless)"),
            "fanless": b(True, "Quiet, fanless operation"),
            "max_power_consumption_w": n(150, "150 W including PoE output; 20 W excluding PoE output"),
            "mac_address_table": t("16384 entries"),
        },
    },
    "USW-16-PoE": {"source": "poe_gen2", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-24-POE (95W)": {"source": "poe_gen2", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-48-POE (195W)": {"source": "poe_gen2", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-48-PoE": {"source": "poe_gen2", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-24": {"source": "usw24", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-48": {"source": "usw48", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
    "USW-Pro-24": {"source": "pro", "values": {"fan_design": t("Fanless passive cooling"), "fanless": b(True)}},
    "USW-Pro-48": {"source": "pro", "values": {"fan_design": t("Fanless passive cooling"), "fanless": b(True)}},
    "USW-Aggregation": {"source": "aggregation", "values": {"fan_design": t("Fanless"), "fanless": b(True)}},
}


class Command(BaseCommand):
    help = "Import official fan/cooling specifications for Ubiquiti switch gaps."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        codes = {code for item in MODELS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, url in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version="Official exact-model UniFi datasheet, verified 2026-10-22",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Ubiquiti UniFi switch datasheet ({key})",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {model}")
            model_new = model_corrected = 0
            url = SOURCES[item["source"]]
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                old_value = None
                if had:
                    old_value = (
                        existing.value_text
                        if existing.value_text
                        else existing.value_number
                        if existing.value_number is not None
                        else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": url[:200],
                    "source_note": "Manually verified from Ubiquiti's official exact-model datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["source"]],
                    source_location=f"Official datasheet cooling/hardware section - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models={len(MODELS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
