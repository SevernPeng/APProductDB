from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "FS728TP": {
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/FS526T-FS726T-FS728TLP-FS728TP-FS750T2.pdf",
        "title": "NETGEAR Fast Ethernet Smart Switches FS526T, FS728TLP, FS728TP and FS750T2 datasheet",
        "version": "DS-FS526T, FS728TLP, FS728TP, FS750T2-9Feb21; accessed 2026-10-20",
        "location": "pp. 2-8, FS728TP column",
    },
    "GC110": {
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/gc110_gc110p_gc510p_gc510pp_ds.pdf",
        "title": "NETGEAR GC110, GC110P, GC510P and GC510PP datasheet",
        "version": "DS-GC110/GC110P/GC510P/GC510PP-14Jan21; accessed 2026-10-20",
        "location": "pp. 3-16, GC110 column",
    },
    "MS108EUP": {
        "url": "https://www.downloads.netgear.com/files/GDC/MS108EUP/MS108EUP_DS.pdf",
        "title": "NETGEAR MS108EUP 8-port Ultra60 PoE++ Multi-Gigabit Ethernet Plus Switch datasheet",
        "version": "Official NETGEAR MS108EUP datasheet; accessed 2026-10-20",
        "location": "pp. 1 and 3-4, technical specifications",
    },
}


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


def na(raw="Not applicable"):
    return "not_applicable", None, raw


PRODUCTS = {
    "FS728TP": {
        "ethernet_interfaces": t("24 x 10/100BASE-TX RJ45; 2 x dedicated 10/100/1000BASE-T RJ45; 2 x combo 1G copper/SFP"),
        "uplink_interfaces": t("2 x dedicated 1G copper and 2 x combo 1G copper/SFP uplink ports"),
        "poe_standard": t("IEEE 802.3af PoE"),
        "poe_ports": n(24),
        "poe_budget_w": n(192),
        "max_poe_per_port_w": n(15.4),
        "poe_configuration": t("24 x IEEE 802.3af PoE ports; 192 W total PoE budget; PoE timer"),
        "switching_capacity_gbps": n(12.8),
        "packet_buffer_mb": n(1),
        "jumbo_frame_bytes": n(2048, "2K jumbo frame support"),
        "mac_address_table": t("4K"),
        "vlan_count": n(128),
        "igmp_group_capacity": t("512 multicast groups"),
        "lag_group_capacity": t("8 LACP LAGs with up to 8 members per LAG; 6 static LAGs with up to 8 members"),
        "l2_features": t(
            "IEEE 802.1Q, IP- and MAC-based VLANs; voice VLAN; LACP and static LAGs; IGMPv1/v2/v3 "
            "snooping and querier; protected ports; LLDP/LLDP-MED; port mirroring; QoS"
        ),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU guard"),
        "acl_security": t(
            "IP-, MAC- and L4-based ACLs; 802.1X/RADIUS; MAC lockdown; protected ports; DHCP filtering; DoS protection"
        ),
        "dhcp_features": t("DHCP client and DHCP filtering"),
        "management_methods": t("Web GUI; Smart Control Center; NMS300; SNMP v1/v2c/v3; RMON; TFTP/HTTP"),
        "dimensions_mm": t("440 x 257 x 43 mm (W x D x H)"),
        "power_supply": t("Fixed internal AC power supply"),
        "max_power_consumption_w": n(256, "Worst case, all ports used, line-rate traffic, maximum PoE"),
        "fan_design": t("1 variable-speed fan; 38.1 dBA at 25 °C"),
        "fanless": b(False),
        "operating_temperature_c": t("0 to 40 °C"),
    },
    "GC110": {
        "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45; 2 x dedicated 100M/1G SFP"),
        "uplink_interfaces": t("2 x dedicated 100M/1G SFP"),
        "poe_standard": na("GC110 is the non-PoE model"),
        "poe_ports": na("GC110 is the non-PoE model"),
        "poe_budget_w": na("GC110 is the non-PoE model"),
        "max_poe_per_port_w": na("GC110 is the non-PoE model"),
        "poe_configuration": na("GC110 is the non-PoE model"),
        "cpu": t("400 MHz Cortex-A9 single-core CPU"),
        "dram_memory": t("256 MB RAM"),
        "flash_memory": t("8 MB SPI flash and 256 MB NAND flash"),
        "switching_capacity_gbps": n(20),
        "packet_forwarding_rate_mpps": n(14.9),
        "packet_buffer_mb": n(1.5),
        "jumbo_frame_bytes": n(9216),
        "mac_address_table": t("16K dynamic entries"),
        "vlan_count": n(256),
        "igmp_group_capacity": t("512 multicast groups"),
        "arp_entry_capacity": t("384 ARP and 128 NDP entries"),
        "ip_interface_capacity": t("15 routed VLAN interfaces"),
        "routing_entry_capacity": t("32 IPv4 and 31 IPv6 static routes"),
        "lag_group_capacity": t("5 static or LACP LAGs; up to 8 members per LAG"),
        "l2_features": t(
            "IEEE 802.1Q, MAC, dynamic, voice, video, protocol and private VLANs; LACP; IGMPv1/v2/v3 "
            "and MLDv1/v2 snooping; LLDP/LLDP-MED; storm control; port mirroring; QoS"
        ),
        "l3_features": t("IPv4 and IPv6 static routing; VLAN routing; IRDP"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
        "acl_security": t(
            "100 shared MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; RADIUS/TACACS+; MAC lockdown"
        ),
        "dhcp_features": t("DHCP client, Layer 2 DHCP relay and DHCP snooping with up to 8K bindings"),
        "management_methods": t("NETGEAR Insight app/Cloud Portal; local web GUI; SNMP/RMON; TFTP/HTTP; syslog"),
        "dimensions_mm": t("245 x 123 x 33 mm (W x D x H)"),
        "power_supply": t("External 12 V / 1.5 A power adapter"),
        "max_power_consumption_w": n(10.1),
        "fan_design": t("Fanless; 0 dBA"),
        "fanless": b(True),
        "operating_temperature_c": t("0 to 45 °C"),
    },
    "MS108EUP": {
        "ethernet_interfaces": t("8 x 100M/1G/2.5GBASE-T RJ45"),
        "poe_standard": t("IEEE 802.3af/802.3at/802.3bt (PoE/PoE+/PoE++)"),
        "poe_ports": n(8),
        "poe_budget_w": n(230),
        "max_poe_per_port_w": n(60),
        "poe_configuration": t("Ports 1-4: up to 60 W PoE++; ports 5-8: up to 30 W PoE+; 230 W total budget"),
        "switching_capacity_gbps": n(40),
        "packet_buffer_mb": n(1.5),
        "jumbo_frame_bytes": n(12000),
        "mac_address_table": t("16K"),
        "vlan_count": n(64),
        "igmp_group_capacity": t("128 multicast groups"),
        "lag_group_capacity": t("4 LAGs; up to 4 members per LAG; IEEE 802.3ad LACP"),
        "l2_features": t(
            "IEEE 802.1Q and port-based VLANs; LACP; IGMPv1/v2/v3 snooping; block unknown multicast; "
            "loop prevention; broadcast storm control; port mirroring; QoS"
        ),
        "acl_security": t("Automatic denial-of-service prevention; system password; broadcast storm control"),
        "dhcp_features": t("DHCP client"),
        "management_methods": t("Web browser-based management GUI; configuration upload"),
        "dimensions_mm": t("210 x 140 x 40 mm (W x D x H)"),
        "power_supply": t("External power adapter"),
        "max_power_consumption_w": n(230, "Official product page: maximum power, worst case, all ports used, line-rate traffic"),
        "fan_design": t("Fanless; 0 dBA"),
        "fanless": b(True),
        "operating_temperature_c": t("0 to 40 °C"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR FS728TP, GC110 and MS108EUP specifications."

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
        documents = {}
        for model, source_data in SOURCES.items():
            documents[model], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"], document_version=source_data["version"],
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": source_data["title"], "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            source_data = SOURCES[model]
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
                    "source_url": source_data["url"][:200],
                    "source_note": f"Manually verified from the official NETGEAR datasheet: {source_data['location']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                elif kind == "not_applicable":
                    new_value = None; defaults["value_status"] = ProductSpec.ValueStatus.NOT_APPLICABLE
                    defaults["normalized_value"] = ""
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had and kind != "not_applicable":
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[model],
                    source_location=f"{source_data['location']} - {model} - {code}",
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
