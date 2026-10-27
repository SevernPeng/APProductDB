from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


UNMANAGED = {
    "l2_features": t("Unmanaged Layer 2 Ethernet forwarding; no configurable L2 features"),
    "vlan_count": n(0, "Unmanaged switch; no configurable VLANs"),
    "stp_features": t("Not supported (unmanaged switch)"),
    "acl_security": t("Not supported (unmanaged switch)"),
    "management_methods": t("Unmanaged; no management interface"),
}


PRODUCTS = {
    "TI-G62": {
        "url": "https://downloads.trendnet.com/TI-G62_v2/datasheet/EN_datasheet_TI-G62_%28v2.xR%29.pdf",
        "version": "V2 (v2.xR), updated 2024-12-13",
        "values": {
            **UNMANAGED,
            "switching_capacity_gbps": n(14),
            "packet_forwarding_rate_mpps": n(10.4),
            "packet_buffer_mb": n(0.25, "Data RAM buffer: 256 KB"),
            "mac_address_table": t("4K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frame: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "power_supply": t("Dual redundant 12-56 V DC terminal inputs; TI-M6024 or TI-S15052 sold separately"),
            "max_power_consumption_w": n(4.5, "4.5 W at 56 V DC"),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("143 x 104 x 36 mm"),
        },
    },
    "TI-G80": {
        "url": "https://download.trendnet.com/TI-G80_v2/datasheet/EN_datasheet_TI-G80_%28v2.xR%29.pdf",
        "version": "V2 (v2.xR), updated 2024-11-01",
        "values": {
            **UNMANAGED,
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "packet_buffer_mb": n(0.5, "Data RAM buffer: 512 KB"),
            "mac_address_table": t("8K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frame: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("Dual redundant 12-56 V DC terminal inputs; TI-M6024 sold separately"),
            "max_power_consumption_w": n(3.36, "3.36 W at 48 V DC"),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("143 x 104 x 36 mm"),
        },
    },
    "TI-PG50": {
        "url": "https://download.trendnet.com/TI-PG50_v2/datasheet/EN_datasheet_TI-PG50_%28v2.xR%29.pdf",
        "version": "V2 (v2.xR), updated 2024-11-12",
        "values": {
            **UNMANAGED,
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "packet_buffer_mb": n(0.122, "Data RAM buffer: 125 KB"),
            "mac_address_table": t("2K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frame: 9 KB"),
            "power_supply": t("Dual redundant 48-56 V DC terminal inputs; TI-S15052 sold separately"),
            "max_power_consumption_w": n(2.24, "2.24 W at 48 V DC without powered devices"),
            "poe_configuration": t("4 x Gigabit PoE+ ports; Mode A pins 1/2/3/6"),
            "poe_ports": n(4),
            "poe_budget_w": n(120, "60-120 W power budget depending on input power supply"),
            "max_poe_per_port_w": n(30, "IEEE 802.3at PoE+: up to 30 W per port"),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("113 x 82 x 31 mm"),
        },
    },
    "TI-G642i": {
        "url": "https://downloads.trendnet.com/TI-G642i_v1.6R/datasheet/EN_datasheet_TI-G642i%28v1.6R%29.pdf",
        "version": "v1.6R",
        "values": {
            "l2_features": t("802.1Q and MAC-based VLAN; port isolation; IGMP snooping/querier/fast leave; LACP; QoS; LLDP; ERPS; loopback detection; port mirroring"),
            "vlan_count": n(256, "Up to 256 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; BPDU filter, guard, and root guard"),
            "acl_security": t("ACL by source/destination MAC, source/destination IP, interface, VLAN ID, EtherType, and TCP/UDP port; 802.1X; DHCP snooping; ARP inspection; port security"),
            "management_methods": t("HTTP web GUI; Telnet/SSHv2 CLI; SNMP v1/v2c/v3; RMON; syslog; TRENDnet Hive cloud management"),
            "switching_capacity_gbps": n(12),
            "packet_forwarding_rate_mpps": n(8.92),
            "packet_buffer_mb": n(0.5, "RAM buffer: 512 KB"),
            "mac_address_table": t("8K entries"),
            "jumbo_frame_bytes": n(10240, "Jumbo frames: 10 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless passive cooling"),
            "power_supply": t("Dual redundant 20-60 V DC terminal inputs; compatible external power supplies sold separately"),
            "max_power_consumption_w": n(12),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("160 x 120 x 50 mm"),
        },
    },
    "TEG-30102WS": {
        "url": "https://downloads.trendnet.com/teg-30102ws/datasheet/en_datasheet_teg-30102ws_%28v1.0r%29.pdf",
        "version": "v1.0R, updated 2018-06-18",
        "values": {
            "l2_features": t("802.1Q/private/voice VLAN; LACP; IGMP/MLD snooping; QoS; LLDP; port mirroring; loopback detection; IPv4/IPv6 static routing and inter-VLAN routing"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t("IPv4/IPv6 ACL by MAC, VLAN, ARP/RARP, EtherType, protocol, TCP/UDP port, 802.1p, DSCP, and IP address; up to 256 entries"),
            "management_methods": t("HTTP/HTTPS web GUI; limited console/Telnet/SSHv2 CLI; SNMP v1/v2c/v3; RMON"),
            "switching_capacity_gbps": n(80),
            "packet_forwarding_rate_mpps": n(59.5),
            "packet_buffer_mb": n(2),
            "mac_address_table": t("32K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frames: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("2 hot-swappable smart fans; 41.7 dBA maximum"),
            "power_supply": t("100-240 V AC, 50/60 Hz internal power supply"),
            "max_power_consumption_w": n(27.36),
            "operating_temperature_c": t("0 to 50 °C"),
            "dimensions_mm": t("330 x 230 x 44.45 mm"),
        },
    },
    "TEG-3102WS": {
        "url": "https://downloads.trendnet.com/TEG-3102WS/datasheets/EN_intl_datasheet_TEG-3102WS_%28v1.0R%29.pdf",
        "version": "v1.0R, updated 2022-11-09",
        "values": {
            "l2_features": t("802.1Q/GVRP/private/voice VLAN; static and LACP aggregation; IGMP/MLD snooping; QoS; LLDP; port mirroring; IPv4/IPv6 static and inter-VLAN routing"),
            "vlan_count": n(256, "Up to 256 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t("IPv4 L2-L4 and IPv6 ACL; 802.1X/RADIUS/TACACS+; DHCP snooping; DoS protection; IP-MAC-port binding"),
            "management_methods": t("HTTP/HTTPS web GUI; basic Telnet/SSHv2 CLI; SNMP v1/v2c/v3; RMON"),
            "switching_capacity_gbps": n(80),
            "packet_forwarding_rate_mpps": n(59.52),
            "packet_buffer_mb": n(1.5),
            "mac_address_table": t("16K entries"),
            "jumbo_frame_bytes": n(10240, "Jumbo frames: 10 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("100-240 V AC, 50/60 Hz; official sheet identifies an internal power supply"),
            "max_power_consumption_w": n(152.3, "Official datasheet states 152.3 W; this conflicts with its package adapter listing and is retained verbatim"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("240 x 104 x 27 mm"),
        },
    },
    "TEG-S50ES": {
        "url": "https://download.trendnet.com/TEG-S50ES/datasheet/EN_datasheet_TEG-S50ES_%28v1.0R%29.pdf",
        "version": "v1.0R, updated 2018-12-13",
        "values": {
            "l2_features": t("Port-based/802.1Q/private/asymmetric/voice VLAN; static link aggregation; IGMP snooping; QoS; port mirroring; loopback detection"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP"),
            "management_methods": t("HTTP web GUI; SNMP v1/v2c; cable diagnostics; configuration backup/restore and firmware upload"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "packet_buffer_mb": n(0.122, "RAM buffer: 125 KB"),
            "mac_address_table": t("2K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frames: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("5 V DC, 1 A external adapter; 100-240 V AC input"),
            "max_power_consumption_w": n(3.42),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("100.5 x 82 x 28 mm"),
        },
    },
    "TEG-S80ES": {
        "url": "https://downloads.trendnet.com/TEG-S80ES/datasheet/GE_datasheet_TEG-S80ES_%28V1.0R%29.pdf",
        "version": "v1.0R, updated 2018-12-17",
        "values": {
            "l2_features": t("Port-based/802.1Q/private/asymmetric/voice VLAN; static link aggregation; IGMP snooping; QoS; port mirroring; loopback detection"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP"),
            "management_methods": t("HTTP web GUI; SNMP v1/v2c; cable diagnostics; configuration backup/restore and firmware upload"),
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "packet_buffer_mb": n(0.188, "RAM buffer: 192 KB"),
            "mac_address_table": t("4K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frames: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("5 V DC, 1 A external adapter; 100-240 V AC input"),
            "max_power_consumption_w": n(4.94),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("145 x 82 x 28 mm"),
        },
    },
    "TI-PG102i": {
        "url": "https://download.trendnet.com/TI-PG102i_v1.6/datasheet/EN_datasheet_TI-PG102i_%28v1.6R%29.pdf",
        "version": "v1.6R, updated 2025-04-08",
        "values": {
            "l2_features": t("802.1Q/MAC-based VLAN and port isolation; LACP; IGMP snooping; QoS; LLDP; ERPS; loopback detection; port mirroring"),
            "vlan_count": n(256, "Up to 256 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; BPDU filter, guard, and root guard"),
            "acl_security": t("ACL by MAC/IP/interface/VLAN/EtherType/TCP or UDP port; 802.1X; DHCP snooping; ARP inspection; port security"),
            "management_methods": t("HTTP web GUI; Telnet/SSHv2 CLI; SNMP v1/v2c/v3; RMON; syslog; TRENDnet Hive cloud management"),
            "switching_capacity_gbps": n(20),
            "packet_forwarding_rate_mpps": n(14.88),
            "packet_buffer_mb": n(0.5, "RAM buffer: 512 KB"),
            "mac_address_table": t("8K entries"),
            "jumbo_frame_bytes": n(10240, "Jumbo frames: 10 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless passive cooling"),
            "power_supply": t("Dual redundant 24-57 V DC terminal inputs; external supplies sold separately"),
            "max_power_consumption_w": n(253, "13 W without PoE load; 253 W at full PoE load"),
            "poe_configuration": t("8 x Gigabit IEEE 802.3af/at PoE+ ports; Mode A; priority, scheduling, auto classification, and PD alive check"),
            "poe_ports": n(8),
            "max_poe_per_port_w": n(30),
            "poe_budget_w": n(240, "240 W at 48 V DC input; 124 W at 24 V DC input"),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("160 x 120 x 50 mm"),
        },
    },
    "TPE-224WS (C1.0R)": {
        "url": "https://downloads.trendnet.com/TPE-224WS_c1/datasheet/EN_spec_TPE-224WS%28C1.0R%29.pdf",
        "version": "C1.0R, updated 2015-08-06",
        "values": {
            "l2_features": t("802.1Q/GVRP/asymmetric/private/voice VLAN; static and LACP aggregation; IGMP snooping; QoS; LLDP; port mirroring; loopback detection"),
            "vlan_count": n(256, "Up to 256 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t("IPv4 L2-L4 and IPv6 ACL; 802.1X/RADIUS/TACACS+; DHCP snooping; duplicate address and DoS detection"),
            "management_methods": t("HTTP/HTTPS web GUI; SNMP v1/v2c/v3; RMON; LLDP; virtual cable test"),
            "switching_capacity_gbps": n(12.8),
            "packet_forwarding_rate_mpps": n(9.5),
            "packet_buffer_mb": n(0.5),
            "mac_address_table": t("8K entries"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("2 smart fans; 54 dBA maximum"),
            "power_supply": t("100-240 V AC, 50/60 Hz internal power supply"),
            "max_power_consumption_w": n(239.7),
            "poe_configuration": t("24 x 10/100 PoE ports; ports 1-4 support IEEE 802.3at PoE+; Mode A"),
            "poe_ports": n(24),
            "poe_budget_w": n(193),
            "max_poe_per_port_w": n(30, "30 W on ports 1-4; 15.4 W on ports 5-24"),
            "operating_temperature_c": t("-5 to 50 °C"),
            "dimensions_mm": t("440 x 210 x 44.45 mm"),
        },
    },
    "TPE-30102WS": {
        "url": "https://downloads.trendnet.com/TPE-30102WS/datasheet/EN_datasheet_TPE-30102WS%28v1.0R%29.pdf",
        "version": "v1.0R, updated 2018-06-19",
        "values": {
            "l2_features": t("802.1Q/asymmetric/private/voice VLAN; LACP; IGMP/MLD snooping; QoS; LLDP; port mirroring; loopback detection; IPv4/IPv6 static and inter-VLAN routing"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
            "acl_security": t("IPv4/IPv6 ACL by MAC, VLAN, ARP/RARP, EtherType, protocol, TCP/UDP port, 802.1p, DSCP and IP address; up to 256 entries"),
            "management_methods": t("HTTP/HTTPS web GUI; limited console/Telnet/SSHv2 CLI; SNMP v1/v2c/v3; RMON"),
            "switching_capacity_gbps": n(80),
            "packet_forwarding_rate_mpps": n(59.5),
            "packet_buffer_mb": n(2),
            "mac_address_table": t("32K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frames: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("2 hot-swappable smart fans; 41.7 dBA maximum"),
            "power_supply": t("100-240 V AC, 50/60 Hz internal power supply"),
            "max_power_consumption_w": n(27.36, "27.36 W without PoE load"),
            "poe_configuration": t("8 x 2.5GBASE-T IEEE 802.3af/at PoE+ ports; Mode A; priority, delay, scheduling, and classification controls"),
            "poe_ports": n(8),
            "poe_budget_w": n(240),
            "max_poe_per_port_w": n(30),
            "operating_temperature_c": t("0 to 50 °C"),
            "dimensions_mm": t("330 x 230 x 44.45 mm"),
        },
    },
    "TPE-P521ES": {
        "url": "https://download.trendnet.com/TPE-P521ES/datasheet/EN_intl_datasheet_TPE-P521ES_%28V1.0R%29.pdf",
        "version": "v1.0R, updated 2018-12-18",
        "values": {
            "l2_features": t("Port-based/802.1Q/private/asymmetric/voice VLAN; static aggregation; IGMP snooping; QoS; port mirroring; loopback detection"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP"),
            "acl_security": t("Access control list support advertised; detailed match fields are not specified"),
            "management_methods": t("HTTP web GUI; SNMP v1/v2c; cable diagnostics; configuration backup/restore and firmware upload"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "packet_buffer_mb": n(0.5, "RAM buffer: 512 KB"),
            "mac_address_table": t("2K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frames: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("IEEE 802.3at or 802.3af PoE input only; no external power supply"),
            "max_power_consumption_w": n(20.4, "2.4 W without PoE load; 20.4 W at maximum PoE load"),
            "poe_configuration": t("1 x Gigabit PoE+ PD input; 2 x Gigabit PoE PSE output ports; Mode A; PD auto-classification"),
            "poe_ports": n(2),
            "poe_budget_w": n(18, "18 W with 802.3at input; 8 W with 802.3af input"),
            "max_poe_per_port_w": n(15.4, "PoE output supports class 1/2 devices or one class 0/3 device"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("150 x 97 x 28.6 mm"),
        },
    },
    "TPE-TG50ES": {
        "url": "https://downloads.trendnet.com/TPE-TG50ES_v1/datasheets/EN_intl_datasheet_TPE-TG50ES_%28v1.0R%29.pdf",
        "version": "v1.0R, updated 2019-03-05",
        "values": {
            "l2_features": t("Port-based/802.1Q/private/asymmetric/voice VLAN; static aggregation; IGMP snooping; QoS; port mirroring; loopback detection"),
            "vlan_count": n(32, "Up to 32 VLAN groups; VLAN IDs 1-4094"),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP"),
            "management_methods": t("HTTP web GUI; SNMP v1/v2c; cable diagnostics; configuration backup/restore and firmware upload"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "packet_buffer_mb": n(0.122, "Packet buffer: 125 KB"),
            "mac_address_table": t("2K entries"),
            "jumbo_frame_bytes": n(9216, "Jumbo frame: 9 KB"),
            "transmission_method": t("Store-and-forward"),
            "fan_design": t("Fanless"),
            "power_supply": t("48 V DC, 0.8 A external adapter; 110-240 V AC input"),
            "max_power_consumption_w": n(34),
            "poe_configuration": t("4 x Gigabit IEEE 802.3af/at PoE+ ports; Mode A"),
            "poe_ports": n(4),
            "poe_budget_w": n(31),
            "max_poe_per_port_w": n(30),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("150 x 98 x 28 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified TRENDnet industrial switch specifications from current official datasheets."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="TRENDnet").first()
        if not brand:
            raise CommandError("Missing brand: TRENDnet")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=item["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": "TRENDnet industrial switch official data sheet",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing TRENDnet product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from current official data sheet ({item['version']}).",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"Specifications - {model} - {code}",
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
