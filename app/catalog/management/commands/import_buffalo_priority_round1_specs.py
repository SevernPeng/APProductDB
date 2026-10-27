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
    "lsw5": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-5esl_nbk.html",
        "version": "LSW6-GT-5ESL/NBK official product page; accessed 2026-10-15",
        "title": "Buffalo LSW6-GT-5ESL/NBK Product Specifications",
    },
    "lsw8": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-8esl_nbk.html",
        "version": "LSW6-GT-8ESL/NBK official product page; accessed 2026-10-15",
        "title": "Buffalo LSW6-GT-8ESL/NBK Product Specifications",
    },
}


COMMON = {
    "fanless": b(True, "Fanless chassis"),
    "installation": t("Desktop, wall mount, and rear magnet", "Wall-mount holes and rear magnet"),
    "loop_prevention": b(True, "Loop detection"),
    "operating_temperature_c": t("0°C to 40°C", "Operating environment temperature: 0–40°C"),
    "transmission_method": t("Store-and-forward", "Data transfer method: store-and-forward"),
    "flow_control": t("IEEE 802.3x flow control and half-duplex backpressure", "IEEE 802.3x flow control; backpressure"),
}


PRODUCTS = {
    "LSW6-GT-5ESL": {
        **{code: (value, "lsw5", "Features/specifications") for code, value in COMMON.items()},
        "ethernet_interfaces": (t("5 x 10/100/1000 Mbps RJ45 ports", "5 ports, all Gigabit Ethernet"), "lsw5", "Specifications, ports"),
        "dimensions_mm": (t("121 x 26 x 75 mm", "121 × 26 × 75 mm (W × H × D)"), "lsw5", "Specifications, dimensions"),
        "max_power_consumption_w": (n(3.3, "Maximum 3.3 W"), "lsw5", "Specifications, power consumption"),
    },
    "LSW6-GT-8ESL": {
        **{code: (value, "lsw8", "Features/specifications") for code, value in COMMON.items()},
        "ethernet_interfaces": (t("8 x 10/100/1000 Mbps RJ45 ports", "8 ports, all Gigabit Ethernet"), "lsw8", "Specifications, ports"),
        "dimensions_mm": (t("154 x 26 x 85 mm", "154 × 26 × 85 mm (W × H × D)"), "lsw8", "Specifications, dimensions"),
        "max_power_consumption_w": (n(5.3, "Maximum 5.3 W"), "lsw8", "Specifications, power consumption"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified Buffalo unmanaged-switch specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Buffalo").first()
        if not brand:
            raise CommandError("Missing brand: Buffalo")
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
                    "title": data["title"], "region": "Japan", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )

        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Buffalo product: {model}")
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
                    "source_note": "Manually verified from the cited official Buffalo product page.",
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
