from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value): return "number", value
def t(value): return "text", value


GUIDE_URL = (
    "https://eo-sgp-cos.ruijie.com/zip/ArticleHtml/"
    "%E5%AE%98%E7%BD%91%E5%8F%91%E5%B8%83_1778650752012/PDF/00-pdf/"
    "00-Ruijie%20Reyee%20RG-ES200%20Series%20Switches%20Installation%20Guide%20(V1.8).pdf"
)

COMMON = {
    "management_methods": t("Ruijie Cloud platform, Ruijie Cloud app, and local eWeb management"),
    "l2_features": t("VLAN configuration, port isolation, automatic loop prevention, and PoE port restart where applicable"),
}

PRODUCTS = {
    "RG-ES205GC": {
        "pages": "pp. 24-32 (PDF pages 32-40)",
        "values": {
            **COMMON,
            "power_supply": t("DC power adapter; 100-240 V AC input, 5 V DC / 1 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(5),
            "dimensions_mm": t("119 x 62 x 24 mm"),
        },
    },
    "RG-ES205GC-P": {
        "pages": "pp. 2-5 (PDF pages 10-13); PoE details confirmed by section text",
        "values": {
            **COMMON,
            "power_supply": t("DC power adapter"),
            "fan_design": t("Fanless; natural cooling"),
            "max_poe_per_port_w": n(30),
        },
    },
    "RG-ES208GC": {
        "pages": "pp. 28-32 (PDF pages 36-40)",
        "values": {
            **COMMON,
            "power_supply": t("DC power adapter; 100-240 V AC input, 5 V DC / 1 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(5),
            "dimensions_mm": t("160 x 75 x 24 mm"),
        },
    },
    "RG-ES216GC": {
        "pages": "pp. 20-23 (PDF pages 28-31)",
        "values": {
            **COMMON,
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(12),
            "dimensions_mm": t("440 x 165 x 44 mm"),
        },
    },
    "RG-ES218GC-P": {
        "pages": "pp. 6-10 (PDF pages 14-18)",
        "values": {
            **COMMON,
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("1 fixed fan; front-to-rear airflow"),
            "max_poe_per_port_w": n(30),
            "dimensions_mm": t("300 x 230 x 43.6 mm"),
        },
    },
    "RG-ES224GC": {
        "pages": "pp. 16-19 (PDF pages 24-27)",
        "values": {
            **COMMON,
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("Fanless; natural cooling"),
            "max_power_consumption_w": n(14),
            "dimensions_mm": t("440 x 165 x 44 mm"),
        },
    },
    "RG-ES226GC-P": {
        "pages": "pp. 11-15 (PDF pages 19-23)",
        "values": {
            **COMMON,
            "power_supply": t("Internal fixed 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("2 fixed fans; front-to-rear airflow"),
            "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
            "poe_ports": n(24),
            "poe_budget_w": n(370),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n(400),
            "dimensions_mm": t("440 x 289 x 43.6 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee ES200 specifications from official V1.8 hardware guide."

    def add_arguments(self, parser): parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand: raise CommandError("Missing brand: Reyee")
        codes = {c for row in PRODUCTS.values() for c in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys(): raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=GUIDE_URL, document_version="V1.8, updated 2026-05-13",
            defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.SUPPORT,
                      "title": "Ruijie Reyee RG-ES200 Series Switches Installation Guide V1.8",
                      "region": "Global", "published_date": None, "accessed_date": accessed, "active": True},
        )
        written = new = corrected = unchanged = 0
        detail = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product: continue
            mn = mc = 0
            for code, (kind, value) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and
                           (bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None))
                old_value = None if not had else old.value_text if old.value_text else old.value_number
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                            "value_boolean": None, "normalized_value": str(value), "unit": definition.unit,
                            "raw_value": str(value), "source_url": GUIDE_URL[:200],
                            "source_note": "Manually verified from the May 2026 official Reyee hardware guide; model columns and continuation pages visually checked.",
                            "verified_date": accessed}
                if kind == "number": defaults["value_number"] = Decimal(str(value)); value2 = Decimal(str(value))
                else: defaults["value_text"] = str(value); value2 = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had: new += 1; mn += 1
                elif old_value != value2: corrected += 1; mc += 1
                else: unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source, source_location=f"{row['pages']} - {model}",
                    defaults={"source_excerpt": f"{definition.display_name}: {value}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()},
                )
                written += 1
            detail.append(f"{model}:+{mn}/corrected:{mc}")
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"))
        self.stdout.write("; ".join(detail))
