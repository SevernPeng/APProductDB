from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.netgear.com/images/datasheet/switches/GS108Tv3_GS110TPv3_DS.pdf"
MANUAL_URL = "https://www.downloads.netgear.com/files/GDC/GS108Tv3/GS108Tv3_GS110TPv3_GS110TPP_UM_EN.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


def na(raw="Not applicable"):
    return "not_applicable", None, raw


def u(raw="Corrupt legacy value; no replacement is published in the verified official source"):
    return "unknown", None, raw


COMMON = {
    "cpu": t("500 MHz single-core CPU"),
    "dram_memory": t("128 MB RAM"),
    "flash_memory": t("32 MB SPI flash"),
    "packet_buffer_mb": n(0.512, "512 KB packet buffer"),
    "jumbo_frame_bytes": n(10240, "Up to 10K packet size"),
    "mac_address_table": t("8K"),
    "vlan_count": n(64),
    "igmp_group_capacity": t("256 multicast groups"),
    "arp_entry_capacity": t("512 ARP/NDP cache entries"),
    "ip_interface_capacity": u(),
    "routing_entry_capacity": t("32 IPv4 static routes"),
    "lag_group_capacity": t("8 LAGs; up to 8 members per LAG"),
    "link_aggregation": t("IEEE 802.3ad LACP and manual static LAGs"),
    "l2_features": t(
        "IEEE 802.1Q; protocol-, MAC-, voice- and video VLANs; LACP; IGMPv1/v2/v3 and "
        "MLDv1/v2 snooping; LLDP/LLDP-MED; port mirroring; QoS; loop detection"
    ),
    "l3_features": t("IPv4 static and VLAN routing; 32 IPv4 static routes; IRDP"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
    "acl_security": t(
        "100 shared ingress MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; "
        "DHCP snooping; MAC lockdown; DoS prevention; protected ports"
    ),
    "dhcp_features": t("DHCP client and DHCP snooping with 256 bindings"),
    "management_methods": t(
        "NETGEAR Insight app and Cloud Portal; local Web GUI; Smart Control Center; NMS300; "
        "SNMP v1/v2c/v3; RMON; TFTP/HTTP; Syslog"
    ),
    "fan_design": t("Fanless; 0 dBA"),
    "fanless": b(True, "Fanless; 0 dBA"),
}


PRODUCTS = {
    "GS108Tv3": {
        **COMMON,
        "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45; port 1 can accept PoE PD input"),
        "switching_capacity_gbps": n(16),
        "packet_forwarding_rate_mpps": n(11.9),
        "poe_standard": na("No PoE output; port 1 can accept PoE PD input"),
        "poe_ports": na("No PoE output ports"),
        "poe_budget_w": na("No PoE output budget"),
        "max_poe_per_port_w": na("No PoE output ports"),
        "poe_configuration": t("No PoE output; port 1 can receive PoE power from a PSE switch"),
        "max_power_consumption_w": n(5.5),
        "power_supply": t("External 12 V DC, 1.0 A; alternatively PoE PD input on port 1"),
        "dimensions_mm": t("158 x 101 x 27 mm (W x D x H)"),
        "operating_temperature_c": t("0 to 45 °C"),
    },
    "GS110TPv3": {
        **COMMON,
        "ethernet_interfaces": t("8 x 10/100/1000BASE-T PoE+ RJ45; 2 x dedicated 1G SFP"),
        "uplink_interfaces": t("2 x dedicated 100/1000BASE-X SFP"),
        "console_interfaces": u(),
        "switching_capacity_gbps": n(20),
        "packet_forwarding_rate_mpps": n(14.8),
        "poe_standard": t("IEEE 802.3af PoE / IEEE 802.3at PoE+"),
        "poe_ports": n(8),
        "poe_budget_w": n(55),
        "max_poe_per_port_w": n(30),
        "poe_configuration": t("8 x PoE+ ports; 55 W total PoE budget; per-port controls and scheduling"),
        "max_power_consumption_w": n(69.5, "69.5 W maximum with full PoE load"),
        "power_supply": t("External 54 V DC, 1.25 A power adapter"),
        "dimensions_mm": t("236 x 101 x 27 mm (W x D x H)"),
        "operating_temperature_c": t("0 to 45 °C"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR GS108Tv3 and GS110TPv3 specifications."
    document_version = "Official NETGEAR datasheet and user manual; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL, document_version=self.document_version,
            defaults={
                "brand": brand, "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "NETGEAR GS108Tv3 and GS110TPv3 datasheet",
                "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
            },
        )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in values.items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_status = existing.value_status if existing else None
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": SOURCE_URL[:200],
                    "source_note": (
                        "Manually verified from the official NETGEAR datasheet, pp. 3 and 8-12; "
                        f"hardware manual cross-check: {MANUAL_URL}"
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                elif kind in {"unknown", "not_applicable"}:
                    new_value = None
                    defaults["value_status"] = (
                        ProductSpec.ValueStatus.UNKNOWN if kind == "unknown"
                        else ProductSpec.ValueStatus.NOT_APPLICABLE
                    )
                    defaults["normalized_value"] = ""
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had and kind not in {"unknown", "not_applicable"}:
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"pp. 3 and 8-12 - {model} specifications - {code}",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
