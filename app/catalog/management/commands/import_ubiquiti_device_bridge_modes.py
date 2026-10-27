from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


HELP_URL = "https://help.ui.com/hc/en-us/articles/32064746398999-Understanding-Connectivity-Roles-of-UDB-Devices"
SECTOR_URL = "https://eu.store.ui.com/eu/en/category/wifi-bridging/products/udb-pro-sector"

MODELS = {
    "Device Bridge Pro": {
        "url": HELP_URL,
        "values": {
            "bridge_modes": t("PtP AP/client; UniFi AP mesh client; UDB Pro Sector PtMP client"),
            "max_bridge_pairs": n(1, "Point-to-point connection to one other UDB Pro"),
        },
    },
    "UDB-Pro": {
        "url": HELP_URL,
        "values": {
            "bridge_modes": t("PtP AP/client; UniFi AP mesh client; UDB Pro Sector PtMP client"),
            "max_bridge_pairs": n(1, "Point-to-point connection to one other UDB Pro"),
        },
    },
    "Device Bridge Pro Sector": {
        "url": SECTOR_URL,
        "values": {
            "bridge_modes": t("Point-to-multipoint access point; cannot act as a client"),
            "max_bridge_pairs": n(50, "Supports 50+ Device Bridge Pro clients"),
            "beamwidth": t("90° sector antenna"),
        },
    },
    "UDB-Pro-Sector": {
        "url": SECTOR_URL,
        "values": {
            "bridge_modes": t("Point-to-multipoint access point; cannot act as a client"),
            "max_bridge_pairs": n(50, "Supports 50+ Device Bridge Pro clients"),
            "beamwidth": t("90° sector antenna"),
        },
    },
}


class Command(BaseCommand):
    help = "Import official Ubiquiti Device Bridge connectivity-role and sector specifications."

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
        for url, title, doc_type in (
            (HELP_URL, "Ubiquiti Understanding Connectivity Roles of UDB Devices", SourceDocument.DocumentType.OTHER),
            (SECTOR_URL, "Ubiquiti Device Bridge Pro Sector official product page", SourceDocument.DocumentType.PRODUCT_PAGE),
        ):
            documents[url], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version="Official current Ubiquiti page, accessed 2026-10-22",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": doc_type,
                    "title": title,
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
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (bool((existing.value_text or "").strip()) or existing.value_number is not None)
                )
                old_value = (existing.value_text or existing.value_number) if had else None
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from Ubiquiti's official current page.",
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
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"Official connectivity/product specification - {model} - {code}",
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
