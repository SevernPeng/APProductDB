from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


BASE = "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13"
COMMON_9216 = {
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("HTTP/eWeb, Ruijie Cloud, and Ruijie Reyee App; SON supported"),
    "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
    "vlan_count": n(16),
    "l2_features": t(
        "IEEE 802.1Q VLAN, interface flow control, static MAC, interface rate limiting, "
        "port mirroring, and cable test"
    ),
    "acl_security": t(
        "No standard or extended ACL; port isolation, DHCP snooping, storm control, "
        "and CPU protection supported"
    ),
}
COMMON_10000 = {**COMMON_9216, "jumbo_frame_bytes": n(10000)}

PRODUCTS = {
    "RG-ES206GC-P": {
        "values": {
            **COMMON_9216,
            "packet_forwarding_rate_mpps": n(8.9),
            "switching_capacity_gbps": n(12),
            "mac_address_table": t("2000 entries"),
            "power_supply": t("External DC power adapter; 100-240 V AC input; 54 V DC / 1.11 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "poe_configuration": t("4 PoE/PoE+ output ports; 54 W total PoE budget"),
            "poe_ports": n(4),
            "poe_budget_w": n(54),
            "max_power_consumption_w": n(60),
            "dimensions_mm": t("148 x 78 x 26 mm"),
        }
    },
    "RG-ES206GS-P": {
        "values": {
            **COMMON_9216,
            "packet_forwarding_rate_mpps": n(8.9),
            "switching_capacity_gbps": n(12),
            "mac_address_table": t("2000 entries"),
            "power_supply": t("External DC power adapter; 100-240 V AC input; 54 V DC / 1.11 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "poe_configuration": t("4 PoE/PoE+ output ports; 54 W total PoE budget"),
            "poe_ports": n(4),
            "poe_budget_w": n(54),
            "max_power_consumption_w": n(60),
            "dimensions_mm": t("148 x 78 x 26 mm"),
        }
    },
    "RG-ES209GC-P": {
        "values": {
            **COMMON_9216,
            "packet_forwarding_rate_mpps": n(13.4),
            "switching_capacity_gbps": n(18),
            "mac_address_table": t("4000 entries"),
            "power_supply": t("External DC power adapter; 100-240 V AC input; 54 V DC / 2.4 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "poe_configuration": t("8 PoE/PoE+ output ports; 120 W total PoE budget"),
            "poe_ports": n(8),
            "poe_budget_w": n(120),
            "max_power_consumption_w": n(120),
            "dimensions_mm": t("202 x 108 x 28 mm"),
        }
    },
    "RG-ES210GS-P": {
        "values": {
            **COMMON_9216,
            "packet_forwarding_rate_mpps": n(14.8),
            "switching_capacity_gbps": n(20),
            "mac_address_table": t("4000 entries"),
            "power_supply": t("External DC power adapter; 100-240 V AC input; 54 V DC / 2.4 A output"),
            "fan_design": t("Fanless; natural cooling"),
            "poe_configuration": t("8 PoE/PoE+ output ports; 120 W total PoE budget"),
            "poe_ports": n(8),
            "poe_budget_w": n(120),
            "max_power_consumption_w": n(130),
            "dimensions_mm": t("202 x 108 x 28 mm"),
        }
    },
    "RG-ES220GS-P": {
        "values": {
            **COMMON_10000,
            "packet_forwarding_rate_mpps": n(29.7),
            "switching_capacity_gbps": n(40),
            "mac_address_table": t("8000 entries"),
            "power_supply": t("Internal fixed 100-240 V AC power supply"),
            "fan_design": t("1 fixed fan; front-to-rear airflow"),
            "poe_configuration": t("16 PoE/PoE+ output ports; 250 W total PoE budget"),
            "poe_ports": n(16),
            "poe_budget_w": n(250),
            "max_power_consumption_w": n(265),
            "dimensions_mm": t("300 x 223 x 43.6 mm"),
        }
    },
    "RG-ES228GS-P": {
        "values": {
            **COMMON_10000,
            "packet_forwarding_rate_mpps": n(41.6),
            "switching_capacity_gbps": n(56),
            "mac_address_table": t("8000 entries"),
            "power_supply": t("Internal fixed 100-240 V AC power supply"),
            "fan_design": t("1 fixed fan; front-to-rear airflow"),
            "poe_configuration": t("24 PoE/PoE+ output ports; 370 W total PoE budget"),
            "poe_ports": n(24),
            "poe_budget_w": n(370),
            "max_power_consumption_w": n(400),
            "dimensions_mm": t("440 x 214.9 x 44 mm"),
        }
    },
    "RG-ES228GS-LP": {
        "values": {
            **COMMON_10000,
            "packet_forwarding_rate_mpps": n(41.66),
            "switching_capacity_gbps": n(56),
            "mac_address_table": t("8000 entries"),
            "power_supply": t("Internal fixed 100-240 V AC power supply"),
            "fan_design": t("1 fixed fan; front-to-rear airflow"),
            "poe_configuration": t("24 PoE/PoE+ output ports; 250 W total PoE budget"),
            "poe_ports": n(24),
            "poe_budget_w": n(250),
            "max_power_consumption_w": n(302, "< 302 W with PoE full load at 110 V AC"),
            "dimensions_mm": t("440 x 214.9 x 43.2 mm"),
        }
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee ES200 PoE switch specifications (round 14)."

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
        written = new = corrected = unchanged = 0
        detail = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            url = f"{BASE}/{model}_Datasheet_Official_2026-05-13.pdf"
            source, _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version="Official datasheet dated 2026-05-12",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Reyee {model} Official Datasheet",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
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
                    "source_url": url[:200],
                    "source_note": (
                        "Manually verified from the current May 2026 official exact-model datasheet; "
                        "hardware and software tables visually checked."
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
                    source_location=f"Hardware/software specification tables, pp. 5-12 - {model}",
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
