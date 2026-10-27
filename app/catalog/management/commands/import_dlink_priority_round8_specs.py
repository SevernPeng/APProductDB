from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Supported" if value else "Not supported")


SOURCE = "https://www.dlink.com/en/-/media/business_products/dgs/dgs-1510/datasheet/dgs_1510_series_datasheet_en_eu.pdf"


COMMON = {
    "jumbo_frame_bytes": n(9216, "Jumbo frame up to 9,216 bytes"),
    "l2_features": t(
        "IGMP/MLD snooping, 802.3x flow control, loopback detection, 802.3ad link aggregation, "
        "port mirroring, multicast filtering, ERPS, LLDP/LLDP-MED"
    ),
    "l3_features": t("IPv4/IPv6 static routing, default routing, ARP/Gratuitous ARP, IPv6 ND, UDP helper"),
    "multicast_routing": b(False, "No multicast-routing protocol listed; IGMP/MLD snooping only"),
    "operating_temperature_c": t("-5 to 50 °C"),
    "routing_entry_capacity": t("64 IPv4 static routes; 32 IPv6 static routes; 16 IP interfaces"),
    "stacking": t("Physical stacking: up to 6 units, 40 Gbps full duplex; virtual stacking: up to 32 devices"),
    "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP, IEEE 802.1s MSTP; BPDU attack protection"),
    "vlan_count": n(4094, "4K VLAN groups; configurable VID 0-4094"),
}


PRODUCTS = {
    "DGS-1510-28X": {
        "location": "DGS-1510-28X A1 column, pp. 3, 5-6",
        "values": {**COMMON},
    },
    "DGS-1510-28XMP": {
        "location": "DGS-1510-28XMP A1 column, pp. 4-6",
        "values": {**COMMON, "poe_ports": n(24, "Ports 1-24, up to 30 W per port")},
    },
    "DGS-1510-52X": {
        "location": "DGS-1510-52X A2 column, pp. 3, 5-6",
        "values": {
            **COMMON,
            "dimensions_mm": t("440 x 210 x 44 mm"),
            "management_methods": t("Web GUI, CLI/console, Telnet, SNMP v1/v2c/v3, D-Link Network Assistant, RMON"),
            "max_power_consumption_w": n(48, "48 W maximum"),
            "packet_forwarding_rate_mpps": n(130.95),
            "switching_capacity_gbps": n(176),
        },
    },
    "DGS-1510-52XMP": {
        "location": "DGS-1510-52XMP A1 column, pp. 4-6",
        "values": {**COMMON, "poe_ports": n(48, "Ports 1-48, up to 30 W per port")},
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-1510 specifications (round 8)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE,
            document_version="February 2022; exact-model hardware revisions A1/A2; accessed 2026-10-14",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "D-Link DGS-1510 Series Gigabit Stackable Smart Managed Switches Datasheet",
                "region": "Europe/Worldwide",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
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
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": SOURCE[:200],
                    "source_note": "Manually verified from the exact hardware-revision column and shared software table.",
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
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{row['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
