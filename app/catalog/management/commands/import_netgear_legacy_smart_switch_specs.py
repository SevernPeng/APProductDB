from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_GS510TP = "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS510TP.pdf"
URL_GS700T = "https://www.downloads.netgear.com/files/GDC/GS716TV3/GS716Tv3_DS.pdf"
URL_GS516TP = "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS516TP-GS728TP-GS728TPP-GS752TP.pdf"
URL_GS716TP = "https://www.netgear.com/media/GS716TP_GS716TPP_tcm148-89590.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def u(raw="Corrupt legacy value; the verified official source does not publish a replacement"):
    return "unknown", None, raw


GS700T_COMMON = {
    "packet_buffer_mb": n(0.25, "2 Mb packet buffer"),
    "jumbo_frame_bytes": n(9216, "Up to 9K packet size"),
    "mac_address_table": t("16K"),
    "vlan_count": n(256),
    "igmp_group_capacity": t("512 multicast groups"),
    "arp_entry_capacity": t("512 ARP cache entries"),
    "ip_interface_capacity": t("15 routed VLAN interfaces"),
    "routing_entry_capacity": t("32 IPv4 static routes"),
    "lag_group_capacity": t("26 LAGs; up to 8 members per LAG"),
    "l2_features": t(
        "IEEE 802.1Q; protocol-, MAC- and voice VLANs; LACP; IGMPv1/v2/v3 and MLDv1/v2 "
        "snooping; MVR; LLDP/LLDP-MED; port mirroring; QoS"
    ),
    "l3_features": t("IPv4 static and VLAN routing; 32 static routes; 15 routed VLAN interfaces"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
    "acl_security": t(
        "100 shared MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; DHCP snooping; "
        "IP source guard; dynamic ARP inspection; locked-MAC port security; DoS protection"
    ),
    "dhcp_features": t("DHCP client and DHCP snooping; 8K snooping bindings; 1,024 static entries"),
    "management_methods": t(
        "Web GUI (HTTP/HTTPS); Smart Control Center; NMS300; SNMP v1/v2c/v3; RMON; TFTP/HTTP; Syslog"
    ),
    "power_supply": t("Internal AC power supply"),
    "operating_temperature_c": t("0 to 50 °C"),
}


PRODUCTS = {
    "GS510TP": {
        "url": URL_GS510TP,
        "title": "NETGEAR ProSAFE GS510TP datasheet",
        "page": "pp. 1-3",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45; 2 x dedicated 1G SFP"),
            "console_interfaces": u(),
            "ip_interface_capacity": u(),
            "vlan_count": n(64, "64 static IEEE 802.1Q VLAN groups"),
            "l2_features": t(
                "IEEE 802.1Q; manual or LACP link aggregation; IGMPv1/v2/v3 snooping; "
                "LLDP/LLDP-MED; protected ports; port mirroring; QoS; voice VLAN"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t(
                "IP and MAC ACLs; IEEE 802.1X; locked-MAC port security; DHCP filtering; "
                "automatic DoS protection; RADIUS and TACACS+"
            ),
            "dhcp_features": t("DHCP client and DHCP filtering"),
            "management_methods": t(
                "Web GUI (HTTP/HTTPS); Smart Control Center; SNMP v1/v2c/v3; RMON; Syslog"
            ),
            "power_supply": t("Internal universal 100-240 V AC, 50-60 Hz power supply"),
            "operating_temperature_c": t("0 to 50 °C"),
            "fan_design": t("Active cooling; one fan; acoustic noise below 38 dBA"),
        },
    },
    "GS716Tv3": {
        "url": URL_GS700T,
        "title": "NETGEAR GS716T, GS724T and GS748T datasheet (22 Nov 2022 revision)",
        "page": "pp. 3-11",
        "values": {
            **GS700T_COMMON,
            "ethernet_interfaces": t("16 x 10/100/1000BASE-T RJ45; 2 x dedicated 1G SFP"),
            "uplink_interfaces": t("2 x dedicated 100/1000BASE-X SFP"),
            "console_interfaces": u(),
            "switching_capacity_gbps": n(36),
            "max_power_consumption_w": n(14.4),
            "dimensions_mm": t("440 x 204 x 43 mm (W x D x H)"),
            "fan_design": t("Fanless; 0 dBA"),
            "fanless": ("boolean", True, "Fanless; 0 dBA"),
        },
    },
    "GS748T": {
        "url": URL_GS700T,
        "title": "NETGEAR GS716T, GS724T and GS748T datasheet (22 Nov 2022 revision)",
        "page": "pp. 3-11",
        "values": {
            **GS700T_COMMON,
            "ethernet_interfaces": t(
                "48 x 10/100/1000BASE-T RJ45; 2 x dedicated 1G SFP; 2 x combo 1G SFP/RJ45"
            ),
            "uplink_interfaces": t("2 x dedicated 1G SFP plus 2 x combo 1G SFP/RJ45"),
            "console_interfaces": u(),
            "switching_capacity_gbps": n(100),
            "max_power_consumption_w": n(41.1),
            "dimensions_mm": t("440 x 257 x 43 mm (W x D x H)"),
            "fan_design": t("One fan; 37.2 dBA"),
            "fanless": ("boolean", False, "One fan; 37.2 dBA"),
        },
    },
    "GS516TP": {
        "url": URL_GS516TP,
        "title": "NETGEAR ProSAFE GS516TP, GS728TP, GS728TPP and GS752TP datasheet",
        "page": "pp. 1-7",
        "values": {
            "ethernet_interfaces": t(
                "16 x 10/100/1000BASE-T RJ45; ports 1-8 are PoE outputs and ports 15-16 are PoE PD inputs"
            ),
            "uplink_interfaces": t("No dedicated uplink ports; any data port can be used as an uplink"),
            "switching_capacity_gbps": n(32),
            "packet_buffer_mb": n(1, "8 Mb packet buffer"),
            "jumbo_frame_bytes": n(9216, "9K jumbo-frame support"),
            "mac_address_table": t("8K"),
            "vlan_count": n(256),
            "igmp_group_capacity": t("1,024 multicast groups"),
            "arp_entry_capacity": t("1,024 ARP cache entries"),
            "ip_interface_capacity": t("15 routed VLAN interfaces"),
            "routing_entry_capacity": t("32 IPv4 static routes"),
            "lag_group_capacity": t("8 LAGs; up to 8 members per LAG"),
            "l2_features": t(
                "IEEE 802.1Q; LACP; IGMPv1/v2/v3 and MLDv1/v2 snooping; LLDP/LLDP-MED; "
                "port mirroring; QoS; voice and video VLANs"
            ),
            "l3_features": t("IPv4 static and VLAN routing; 32 static routes; 15 routed VLAN interfaces"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t(
                "480 shared MAC, IPv4 and IPv6 ACL rules with L2/L3/L4 matching; 802.1X; "
                "DHCP snooping; locked-MAC port security; network storm protection"
            ),
            "dhcp_features": t(
                "DHCP client and snooping; 8K snooping bindings; 1,024 DHCP static entries"
            ),
            "management_methods": t(
                "Web GUI (HTTP/HTTPS); Smart Control Center; SNMP v1/v2/v3; RMON; TFTP/HTTP; Syslog"
            ),
            "poe_standard": t("IEEE 802.3af PoE output; IEEE 802.3af/at PD input on ports 15-16"),
            "poe_ports": n(8),
            "poe_budget_w": n(76, "Up to 76 W with AC input; up to 22 W pass-through budget"),
            "max_poe_per_port_w": n(15.4),
            "poe_configuration": t(
                "Ports 1-8: IEEE 802.3af PoE output; ports 15-16: PoE PD input; 76 W AC-powered budget"
            ),
            "max_power_consumption_w": n(92.1, "92.1 W worst case with maximum PoE load"),
            "power_supply": t("Internal 100-240 V AC supply; can also be powered through PD ports 15 and/or 16"),
            "dimensions_mm": t("328 x 169 x 43 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 50 °C"),
            "fan_design": t("Active cooling; 24.6 dBA"),
            "fanless": ("boolean", False, "Acoustic noise: 24.6 dBA"),
        },
    },
    "GS716TP": {
        "url": URL_GS716TP,
        "title": "NETGEAR GS716TP and GS716TPP datasheet",
        "page": "pp. 1-10",
        "values": {
            "ethernet_interfaces": t("16 x 10/100/1000BASE-T PoE+ RJ45; 2 x dedicated 1G SFP"),
            "uplink_interfaces": t("2 x dedicated 100/1000BASE-X SFP"),
            "cpu": t("700 MHz single-core CPU"),
            "dram_memory": t("128 MB RAM"),
            "flash_memory": t("32 MB SPI flash"),
            "switching_capacity_gbps": n(36),
            "packet_forwarding_rate_mpps": n(26.8),
            "packet_buffer_mb": n(1.5),
            "jumbo_frame_bytes": n(9216),
            "mac_address_table": t("16K"),
            "vlan_count": n(64),
            "igmp_group_capacity": t("256 multicast groups"),
            "ip_interface_capacity": u(),
            "lag_group_capacity": t("8 LAGs; up to 8 members per LAG"),
            "l2_features": t(
                "IEEE 802.1Q; protocol- and MAC-based VLANs; LACP; IGMPv1/v2/v3 snooping; "
                "LLDP/LLDP-MED; port mirroring; QoS; loop detection"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t(
                "100 shared ingress MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; "
                "DHCP snooping; MAC lockdown; DoS prevention; protected ports"
            ),
            "dhcp_features": t("DHCP client and DHCP snooping with 256 bindings"),
            "management_methods": t(
                "NETGEAR Insight app and Cloud Portal; local Web GUI; Smart Control Center; "
                "SNMP v1/v2c/v3; RMON; HTTP; Syslog"
            ),
            "poe_standard": t("IEEE 802.3af PoE / IEEE 802.3at PoE+"),
            "poe_ports": n(16),
            "poe_budget_w": n(180),
            "max_poe_per_port_w": n(30),
            "poe_configuration": t("16 x PoE+ ports; 180 W total PoE budget; per-port controls and scheduling"),
            "max_power_consumption_w": n(193.9, "193.90 W maximum with full PoE load"),
            "power_supply": t("One fixed internal AC power supply"),
            "dimensions_mm": t("440 x 204 x 43 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 50 °C"),
            "fan_design": t("1 fixed internal temperature- and load-controlled fan; 27.3 dBA at 25 °C"),
            "fanless": ("boolean", False, "One internal fan"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR GS510TP, GS516TP, GS716T/TP and GS748T specifications."
    document_version = "Official NETGEAR datasheet; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            if item["url"] in documents:
                continue
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"], document_version=self.document_version,
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": item["title"], "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
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
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['page']}.",
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
                    product_spec=spec, source_document=documents[item["url"]],
                    source_location=f"{item['page']} - {model} specifications - {code}",
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
