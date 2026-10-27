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
    "s105": {
        "url": "https://www.tendacn.com/us/product/support/S105V10.html",
        "version": "S105 v10.0 current official parameter page and 2025-06-11 datasheet; accessed 2026-10-15",
        "title": "Tenda S105 v10.0 Support and Parameters",
    },
    "s108": {
        "url": "https://www.tendacn.com/de/product/support/s108v8.html",
        "version": "S108 v8.0 current official parameter page and 2025-06-11 datasheet; accessed 2026-10-15",
        "title": "Tenda S108 v8.0 Support and Parameters",
    },
    "s16": {
        "url": "https://www.tendacn.com/eg/product/support/S16",
        "version": "S16 current official parameter page; accessed 2026-10-15",
        "title": "Tenda S16 Support and Parameters",
    },
}


PRODUCTS = {
    "S105": {
        "ethernet_interfaces": (t("5 x 10/100 Mbps Base-TX Ethernet ports", "5*10/100 Base-TX Ethernet ports (Auto MDI/MDIX)"), "s105", "Hardware, Interfaces"),
        "dimensions_mm": (t("82 x 52 x 22.3 mm", "82.0mm x 52.0mm x 22.3mm"), "s105", "Hardware, Dimension"),
        "max_power_consumption_w": (n(1.6, "Max: <1.6 W"), "s105", "Hardware, Power consumption"),
        "fanless": (b(True, "Fan quantity: N/A"), "s105", "Hardware, Fan quantity"),
        "operating_temperature_c": (t("0°C to 45°C", "Operating temperature: 0°C - 45°C"), "s105", "Hardware, Environment"),
    },
    "S108": {
        "dimensions_mm": (t("124 x 59 x 23.1 mm", "124.0mm x 59.0mm x 23.1mm"), "s108", "Hardware, Dimension"),
        "max_power_consumption_w": (n(2.15, "Max: <2.15 W"), "s108", "Hardware, Power consumption"),
        "fanless": (b(True, "Fan quantity: N/A"), "s108", "Hardware, Fan quantity"),
        "operating_temperature_c": (t("0°C to 45°C", "Operating temperature: 0°C - 45°C"), "s108", "Hardware, Environment"),
        "packet_forwarding_rate_mpps": (n(1.19, "1.19 Mpps"), "s108", "Hardware, Packet forwarding rate"),
    },
    "S16": {
        "ethernet_interfaces": (t("16 x 10/100 Mbps Base-TX Ethernet ports", "16*10/100 Base-TX Ethernet ports (Auto MDI/MDIX)"), "s16", "Hardware, Interfaces"),
        "dimensions_mm": (t("218 x 135 x 41.6 mm", "218.0mm x 135.0mm x 41.6mm"), "s16", "Hardware, Dimension"),
        "fanless": (b(True, "Fan quantity: N/A"), "s16", "Hardware, Fan quantity"),
        "switching_capacity_gbps": (n(3.2, "3.2 Gbps"), "s16", "Hardware, Switch capacity"),
        "operating_temperature_c": (t("0°C to 45°C", "Operating temperature: 0°C - 45°C"), "s16", "Hardware, Environment"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified Tenda unmanaged-switch specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Tenda").first()
        if not brand:
            raise CommandError("Missing brand: Tenda")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, data in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=data["url"], document_version=data["version"],
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": data["title"], "region": "Worldwide", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )

        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Tenda product: {model}")
            model_new = model_corrected = 0
            for code, ((kind, value, raw), source_key, location) in values.items():
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
                source = SOURCES[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": source["url"][:200],
                    "source_note": "Manually verified from the cited current official Tenda hardware-version page.",
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
                    product_spec=spec, source_document=documents[source_key],
                    source_location=f"{location} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.B,
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
