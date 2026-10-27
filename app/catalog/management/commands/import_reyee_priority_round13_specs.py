from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value): return "number", value
def t(value): return "text", value


BASE = "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13"
COMMON = {
    "jumbo_frame_bytes": n(9216),
    "power_supply": t("External DC power adapter; 100-240 V AC, 50/60 Hz input; 54 V DC output"),
    "fan_design": t("Fanless; natural cooling"),
    "management_methods": t("HTTP/eWeb, Ruijie Cloud, and Ruijie Reyee App; SON supported"),
    "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
    "vlan_count": n(16),
    "l2_features": t("IEEE 802.1Q VLAN, static aggregation, static MAC, interface flow control, rate limiting, mirroring, and cable test"),
    "acl_security": t("No standard or extended ACL; port isolation, DHCP snooping, storm control, and CPU protection supported"),
}

PRODUCTS = {
    "RG-ES206MG-P": {
        "url": f"{BASE}/RG-ES206MG-P_Datasheet_Official_2026-05-13.pdf",
        "values": {
            **COMMON,
            "packet_forwarding_rate_mpps": n(33.75),
            "mac_address_table": t("4000 entries"),
            "poe_configuration": t("4 PoE/PoE+ output ports; 70 W total PoE budget"),
            "poe_ports": n(4),
            "max_power_consumption_w": n(75.5),
            "dimensions_mm": t("172 x 90.8 x 28 mm"),
        },
    },
    "RG-ES209MG-P": {
        "url": f"{BASE}/RG-ES209MG-P_Datasheet_Official_2026-05-13.pdf",
        "values": {
            **COMMON,
            "packet_forwarding_rate_mpps": n(45),
            "mac_address_table": t("4000 entries"),
            "poe_configuration": t("8 PoE/PoE+ output ports; 130 W total PoE budget"),
            "poe_ports": n(8),
            "max_power_consumption_w": n(138.5),
            "dimensions_mm": t("202 x 108 x 28 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee multi-gigabit ES200 specifications (round 13)."
    def add_arguments(self, parser): parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand: raise CommandError("Missing brand: Reyee")
        codes = {c for row in PRODUCTS.values() for c in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys(): raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate(); written = new = corrected = unchanged = 0; detail = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product: continue
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"], document_version="Official datasheet dated 2026-05-12",
                defaults={"brand": brand, "product": product, "document_type": SourceDocument.DocumentType.DATASHEET,
                          "title": f"Reyee {model} Official Datasheet", "region": "Global",
                          "published_date": None, "accessed_date": accessed, "active": True})
            mn = mc = 0
            for code, (kind, value) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and
                           (bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None))
                old_value = None if not had else old.value_text if old.value_text else old.value_number
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                            "value_boolean": None, "normalized_value": str(value), "unit": definition.unit,
                            "raw_value": str(value), "source_url": row["url"][:200],
                            "source_note": "Manually verified from the current May 2026 official exact-model datasheet; hardware and software tables visually checked.",
                            "verified_date": accessed}
                if kind == "number": defaults["value_number"] = Decimal(str(value)); value2 = Decimal(str(value))
                else: defaults["value_text"] = str(value); value2 = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had: new += 1; mn += 1
                elif old_value != value2: corrected += 1; mc += 1
                else: unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source, source_location=f"Hardware/software specification tables, pp. 6-12 - {model}",
                    defaults={"source_excerpt": f"{definition.display_name}: {value}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()})
                written += 1
            detail.append(f"{model}:+{mn}/corrected:{mc}")
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"))
        self.stdout.write("; ".join(detail))
