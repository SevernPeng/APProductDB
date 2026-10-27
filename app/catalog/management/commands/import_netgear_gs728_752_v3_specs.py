from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.downloads.netgear.com/files/GDC/GS728TPPv3/GS728TPv3_GS728TPPv3_GS752TPv3_GS752TPPv3_DS.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


def u(raw="Corrupt legacy value; no corresponding console interface is published in the official datasheet"):
    return "unknown", None, raw


COMMON = {
    "uplink_interfaces": t("4 x dedicated 1G SFP"),
    "console_interfaces": u(),
    "switch_usb_interfaces": t("1 x USB port for configuration backup and firmware updates"),
    "cpu": t("800 MHz ARM Cortex-A55 single-core"),
    "dram_memory": t("512 MB DDR RAM"),
    "flash_memory": t("64 MB flash"),
    "packet_buffer_mb": n(1.5),
    "jumbo_frame_bytes": n(10240, "Up to 10K packet size"),
    "mac_address_table": t("16K"),
    "vlan_count": n(256),
    "vlan_support": t("IEEE 802.1Q; IP-, MAC-, voice-, dynamic- and private VLANs; up to 256 VLANs"),
    "igmp_group_capacity": t("512 multicast groups"),
    "arp_entry_capacity": t("512 ARP entries"),
    "ip_interface_capacity": t("15 routed VLAN interfaces"),
    "routing_entry_capacity": t("32 IPv4 and 32 IPv6 static routes"),
    "lag_group_capacity": t("16 LAGs; up to 8 members per LAG"),
    "link_aggregation": t("IEEE 802.3ad LACP and manual link aggregation"),
    "l2_features": t(
        "IEEE 802.1Q; LACP; IGMPv1/v2/v3 and MLDv1/v2 snooping; MVR; LLDP/LLDP-MED; "
        "port mirroring; storm control; QoS; voice and private VLANs"
    ),
    "l3_features": t("IPv4/IPv6 static and VLAN routing; IRDP; 15 routed VLAN interfaces"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
    "acl_security": t(
        "100 shared ingress MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; "
        "DHCP snooping; dynamic ARP inspection; locked-MAC port security; DoS protection"
    ),
    "dhcp_features": t("DHCP client; DHCP snooping with 256 bindings; Layer 2 DHCP relay"),
    "management_methods": t(
        "NETGEAR Insight app and Cloud Portal; Web GUI; Lite CLI; SNMP v1/v2c/v3; RMON; "
        "TFTP/HTTP; Syslog"
    ),
    "poe_standard": t("IEEE 802.3af PoE / IEEE 802.3at PoE+"),
    "max_poe_per_port_w": n(30),
    "power_supply": t("One fixed internal AC power supply"),
    "operating_temperature_c": t("0 to 50 °C"),
}


PRODUCTS = {
    "GS728TP": {
        **COMMON,
        "ethernet_interfaces": t("24 x 10/100/1000BASE-T PoE+ RJ45; 4 x dedicated 1G SFP"),
        "switching_capacity_gbps": n(56),
        "packet_forwarding_rate_mpps": n(41.67),
        "poe_ports": n(24),
        "poe_budget_w": n(190),
        "poe_configuration": t("24 x PoE+ ports; 190 W total PoE budget"),
        "max_power_consumption_w": n(226, "226 W maximum with full PoE load"),
        "dimensions_mm": t("440 x 257 x 43.2 mm (W x D x H)"),
        "fan_design": t("2 fixed internal fans; 26.8 dBA at 25 °C"),
        "fanless": b(False, "2 fixed internal fans"),
    },
    "GS752TP": {
        **COMMON,
        "ethernet_interfaces": t("48 x 10/100/1000BASE-T PoE+ RJ45; 4 x dedicated 1G SFP"),
        "switching_capacity_gbps": n(104),
        "packet_forwarding_rate_mpps": n(77.38),
        "poe_ports": n(48),
        "poe_budget_w": n(380),
        "poe_configuration": t("48 x PoE+ ports; 380 W total PoE budget"),
        "max_power_consumption_w": n(431, "431 W maximum with full PoE load"),
        "dimensions_mm": t("440 x 310 x 43.2 mm (W x D x H)"),
        "fan_design": t("2 fixed internal fans; 36.6 dBA at 25 °C"),
        "fanless": b(False, "2 fixed internal fans"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified current NETGEAR GS728TPv3 and GS752TPv3 specifications."
    document_version = "Official NETGEAR v3 datasheet, 25 March 2026; accessed 2026-10-20"

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
                "title": "NETGEAR GS728TPv3, GS728TPPv3, GS752TPv3 and GS752TPPv3 datasheet",
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
                    "source_note": "Manually verified from the official NETGEAR v3 datasheet, pp. 3 and 8-13.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                elif kind == "unknown":
                    new_value = None
                    defaults["value_status"] = ProductSpec.ValueStatus.UNKNOWN
                    defaults["normalized_value"] = ""
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had and kind != "unknown":
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"pp. 3 and 8-13 - {model} specifications - {code}",
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
