from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "ei_1505": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000085149/DS-3E1505P-EI_Datasheet_20231023.pdf",
        "version": "2023-10-23",
        "title": "Hikvision DS-3E1505P-EI Datasheet",
    },
    "ei_1508": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000034945/DS-3E1508-EI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "title": "Hikvision DS-3E1508-EI Datasheet",
    },
    "ei_1510": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000034948/DS-3E1510P-EI-V2_Datasheet_20231023.pdf",
        "version": "2023-10-23 V2",
        "title": "Hikvision DS-3E1510P-EI V2 Datasheet",
    },
    "ei_1516_2026": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000034944/DS-3E1516-EI_Datasheet_20260119.pdf",
        "version": "2026-01-19",
        "title": "Hikvision DS-3E1516-EI Datasheet",
    },
    "ei_1518_2026": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000034947/DS-3E1518P-EI_Datasheet_20260119.pdf",
        "version": "2026-01-19",
        "title": "Hikvision DS-3E1518P-EI Datasheet",
    },
    "ei_1524": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000034943/DS-3E1524-EI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "title": "Hikvision DS-3E1524-EI Datasheet",
    },
    "industrial_1506_2025": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000163902/DS-3T1506HP-SI-4P2F_Datasheet_20251111.pdf",
        "version": "2025-11-11",
        "title": "Hikvision DS-3T1506HP-SI-4P2F Datasheet",
    },
    "industrial_1510_2025": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000168827/DS-3T1510P-SI-FLT_Datasheet_20250928.pdf",
        "version": "2025-09-28",
        "title": "Hikvision DS-3T1510P-SI-FLT Datasheet",
    },
    "ei_1526_2026": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000034946/DS-3E1526P-EI_Datasheet_20260119.pdf",
        "version": "2026-01-19",
        "title": "Hikvision DS-3E1526P-EI Datasheet",
    },
    "ei_m_1518": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000005201/OFR013776/M000081862/Data_Sheet/DS-3E1518P-EI_M_Datasheet_20240428.pdf",
        "version": "2024-04-28",
        "title": "Hikvision DS-3E1518P-EI/M Datasheet",
    },
    "ei_m_1526": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000081863/DS-3E1526P-EI_M_Datasheet_20240428.pdf",
        "version": "2024-04-28",
        "title": "Hikvision DS-3E1526P-EI/M Datasheet",
    },
    "industrial_2506": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000161024/DS-3T2506P_Datasheet_20250815.pdf",
        "version": "2025-08-15",
        "title": "Hikvision DS-3T2506P Datasheet",
    },
    "si_1518": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000043338/DS-3E1518P-SI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "title": "Hikvision DS-3E1518P-SI Datasheet",
    },
    "ei_1506": {
        "url": "https://www.hikvision.com/content/dam/hikvision/th/datasheet/DS-3E1506P-EI_Datasheet_20231023-1.pdf",
        "version": "2023-10-23",
        "title": "Hikvision DS-3E1506P-EI Datasheet",
    },
    "si_1526": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000005201/OFR011810/M000043339/Data_Sheet/DS-3E1526P-SI_Datasheet_20240514.pdf",
        "version": "2024-05-14",
        "title": "Hikvision DS-3E1526P-SI Datasheet",
    },
    "si_1526_page": {
        "url": "https://pro-av.hikvision.com/mena-en/products/transmission/Network-Switches/smart-managed-series/ds-3e1526p-si/",
        "version": "Current product page accessed 2026-10-12",
        "title": "Hikvision DS-3E1526P-SI Product Page",
        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "region": "Middle East and Africa",
    },
}


def n(value, source):
    return "number", value, source


def t(value, source):
    return "text", value, source


EI_M_COMMON = {
    "switching_capacity_gbps": n(56, "ei_m_1518"),
    "packet_forwarding_rate_mpps": n(41.66, "ei_m_1518"),
    "mac_address_table": t("8K entries", "ei_m_1518"),
    "packet_buffer_mb": n(0.513, "ei_m_1518"),
    "management_methods": t("Web management; Hik-Partner Pro remote/cloud management; Super IP", "ei_m_1518"),
    "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m; PoE usage visibility in Hik-Partner Pro", "ei_m_1518"),
    "poe_standard": t("IEEE 802.3af/at", "ei_m_1518"),
    "max_poe_per_port_w": n(30, "ei_m_1518"),
    "vlan_count": n(32, "ei_m_1518"),
    "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_m_1518"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_m_1518"),
    "dimensions_mm": t("440.0 x 220.8 x 44.0 mm", "ei_m_1518"),
    "operating_temperature_c": t("0 to 45 °C", "ei_m_1518"),
}


MODELS = {
    "DS-3E1505P-EI": {
        "switching_capacity_gbps": n(10, "ei_1505"),
        "packet_forwarding_rate_mpps": n(7.44, "ei_1505"),
        "mac_address_table": t("2K entries", "ei_1505"),
        "packet_buffer_mb": n(0.125, "ei_1505"),
        "power_supply": t("54 V DC, 1.2 A", "ei_1505"),
        "fan_design": t("Fanless metal enclosure", "ei_1505"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP", "ei_1505"),
        "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m; scheduled PoE", "ei_1505"),
        "poe_standard": t("IEEE 802.3af/at", "ei_1505"),
        "poe_ports": n(4, "ei_1505"),
        "poe_budget_w": n(60, "ei_1505"),
        "max_poe_per_port_w": n(30, "ei_1505"),
        "vlan_count": n(32, "ei_1505"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_1505"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1505"),
        "max_power_consumption_w": n(65, "ei_1505"),
        "dimensions_mm": t("121.1 x 27.6 x 83.1 mm", "ei_1505"),
        "operating_temperature_c": t("0 to 40 °C", "ei_1505"),
    },
    "DS-3E1508-EI": {
        "switching_capacity_gbps": n(16, "ei_1508"),
        "packet_forwarding_rate_mpps": n(11.91, "ei_1508"),
        "mac_address_table": t("4K entries", "ei_1508"),
        "packet_buffer_mb": n(0.188, "ei_1508"),
        "power_supply": t("5 V DC, 1 A", "ei_1508"),
        "fan_design": t("Fanless", "ei_1508"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP", "ei_1508"),
        "vlan_count": n(32, "ei_1508"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_1508"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1508"),
        "max_power_consumption_w": n(5, "ei_1508"),
        "dimensions_mm": t("170.0 x 27.6 x 93.1 mm", "ei_1508"),
        "operating_temperature_c": t("0 to 40 °C", "ei_1508"),
    },
    "DS-3E1510P-EI": {
        "switching_capacity_gbps": n(20, "ei_1510"),
        "packet_forwarding_rate_mpps": n(14.88, "ei_1510"),
        "mac_address_table": t("4K entries", "ei_1510"),
        "packet_buffer_mb": n(0.188, "ei_1510"),
        "power_supply": t("54 V DC, 2.22 A", "ei_1510"),
        "fan_design": t("Fanless metal enclosure", "ei_1510"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP", "ei_1510"),
        "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m", "ei_1510"),
        "poe_standard": t("IEEE 802.3af/at", "ei_1510"),
        "poe_ports": n(8, "ei_1510"),
        "poe_budget_w": n(110, "ei_1510"),
        "max_poe_per_port_w": n(30, "ei_1510"),
        "vlan_count": n(32, "ei_1510"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_1510"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1510"),
        "max_power_consumption_w": n(120, "ei_1510"),
        "dimensions_mm": t("217.6 x 27.6 x 108.5 mm", "ei_1510"),
        "operating_temperature_c": t("0 to 40 °C", "ei_1510"),
    },
    "DS-3E1516-EI": {
        "switching_capacity_gbps": n(56, "ei_1516_2026"),
        "packet_forwarding_rate_mpps": n(41.66, "ei_1516_2026"),
        "mac_address_table": t("8K entries", "ei_1516_2026"),
        "packet_buffer_mb": n(0.513, "ei_1516_2026"),
        "power_supply": t("220 V AC, 50/60 Hz, maximum 0.3 A", "ei_1516_2026"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; DHCP client; Super IP", "ei_1516_2026"),
        "vlan_count": n(32, "ei_1516_2026"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; QoS; port mirroring", "ei_1516_2026"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1516_2026"),
        "acl_security": t("DHCP snooping; port isolation", "ei_1516_2026"),
        "max_power_consumption_w": n(12, "ei_1516_2026"),
        "dimensions_mm": t("335.0 x 44.5 x 175.8 mm", "ei_1516_2026"),
        "operating_temperature_c": t("0 to 45 °C", "ei_1516_2026"),
    },
    "DS-3E1518P-EI": {
        "switching_capacity_gbps": n(56, "ei_1518_2026"),
        "packet_forwarding_rate_mpps": n(41.66, "ei_1518_2026"),
        "mac_address_table": t("8K entries", "ei_1518_2026"),
        "packet_buffer_mb": n(0.513, "ei_1518_2026"),
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 4 A", "ei_1518_2026"),
        "management_methods": t("Web; Hik-Partner Pro; DHCP client; Super IP", "ei_1518_2026"),
        "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m; scheduled PoE", "ei_1518_2026"),
        "poe_standard": t("IEEE 802.3af/at", "ei_1518_2026"),
        "poe_ports": n(16, "ei_1518_2026"),
        "poe_budget_w": n(230, "ei_1518_2026"),
        "max_poe_per_port_w": n(30, "ei_1518_2026"),
        "vlan_count": n(32, "ei_1518_2026"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; QoS; port mirroring", "ei_1518_2026"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1518_2026"),
        "acl_security": t("DHCP snooping; port isolation", "ei_1518_2026"),
        "max_power_consumption_w": n(250, "ei_1518_2026"),
        "dimensions_mm": t("440.0 x 44.0 x 220.8 mm", "ei_1518_2026"),
        "operating_temperature_c": t("0 to 45 °C", "ei_1518_2026"),
    },
    "DS-3E1524-EI": {
        "switching_capacity_gbps": n(56, "ei_1524"),
        "packet_forwarding_rate_mpps": n(41.66, "ei_1524"),
        "mac_address_table": t("8K entries", "ei_1524"),
        "packet_buffer_mb": n(0.513, "ei_1524"),
        "power_supply": t("220 V AC, 50/60 Hz, maximum 0.7 A", "ei_1524"),
        "fan_design": t("Fanless", "ei_1524"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP", "ei_1524"),
        "vlan_count": n(32, "ei_1524"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_1524"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1524"),
        "max_power_consumption_w": n(13, "ei_1524"),
        "dimensions_mm": t("335.0 x 44.5 x 175.8 mm", "ei_1524"),
        "operating_temperature_c": t("0 to 45 °C", "ei_1524"),
    },
    "DS-3T1506HP-SI-4P2F": {
        "switching_capacity_gbps": n(20, "industrial_1506_2025"),
        "packet_forwarding_rate_mpps": n(14.88, "industrial_1506_2025"),
        "mac_address_table": t("8K entries", "industrial_1506_2025"),
        "packet_buffer_mb": n(0.513, "industrial_1506_2025"),
        "power_supply": t("48 V DC, dual inputs and hot backup; 52-57 V recommended", "industrial_1506_2025"),
        "fan_design": t("Fanless industrial IP40 enclosure", "industrial_1506_2025"),
        "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m", "industrial_1506_2025"),
        "poe_standard": t("IEEE 802.3bt Hi-PoE", "industrial_1506_2025"),
        "poe_ports": n(4, "industrial_1506_2025"),
        "poe_budget_w": n(300, "industrial_1506_2025"),
        "max_poe_per_port_w": n(90, "industrial_1506_2025"),
        "vlan_count": n(32, "industrial_1506_2025"),
        "l2_features": t("IEEE 802.1Q; static link aggregation; port isolation; QoS; SNMP; cable detection", "industrial_1506_2025"),
        "stp_features": t("STP; RSTP; ERPS; storm control", "industrial_1506_2025"),
        "acl_security": t("DHCP snooping; port isolation", "industrial_1506_2025"),
        "max_power_consumption_w": n(303, "industrial_1506_2025"),
        "dimensions_mm": t("155.0 x 46.0 x 130.0 mm", "industrial_1506_2025"),
        "operating_temperature_c": t("-40 to 75 °C", "industrial_1506_2025"),
        "transmission_method": t("4 Gigabit copper PoE ports; 2 Gigabit SFP fiber ports", "industrial_1506_2025"),
    },
    "DS-3T1510P-SI-FLT": {
        "switching_capacity_gbps": n(20, "industrial_1510_2025"),
        "packet_forwarding_rate_mpps": n(14.88, "industrial_1510_2025"),
        "mac_address_table": t("8K entries", "industrial_1510_2025"),
        "packet_buffer_mb": n(0.513, "industrial_1510_2025"),
        "power_supply": t("48-57 V DC, 7.5 A; dual power inputs", "industrial_1510_2025"),
        "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP", "industrial_1510_2025"),
        "poe_configuration": t("PoE watchdog; long-range PoE up to 300 m", "industrial_1510_2025"),
        "poe_standard": t("IEEE 802.3af/at", "industrial_1510_2025"),
        "poe_ports": n(8, "industrial_1510_2025"),
        "poe_budget_w": n(240, "industrial_1510_2025"),
        "max_poe_per_port_w": n(30, "industrial_1510_2025"),
        "vlan_count": n(4094, "industrial_1510_2025"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; QoS; port mirroring; rate limiting; storm control", "industrial_1510_2025"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; G.8032 ERPS", "industrial_1510_2025"),
        "acl_security": t("ACL up to 64 lists and 128 rules; DHCP snooping; IPSG port/MAC/IP binding; ARP anti-spoofing", "industrial_1510_2025"),
        "max_power_consumption_w": n(250, "industrial_1510_2025"),
        "dimensions_mm": t("180.0 x 25.0 x 134.0 mm", "industrial_1510_2025"),
        "operating_temperature_c": t("-40 to 75 °C", "industrial_1510_2025"),
        "transmission_method": t("8 Gigabit copper PoE ports; 2 Gigabit SFP fiber ports", "industrial_1510_2025"),
    },
    "DS-3E1526P-EI": {
        "switching_capacity_gbps": n(56, "ei_1526_2026"),
        "packet_forwarding_rate_mpps": n(41.66, "ei_1526_2026"),
        "mac_address_table": t("8K entries", "ei_1526_2026"),
        "packet_buffer_mb": n(0.513, "ei_1526_2026"),
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 6.3 A", "ei_1526_2026"),
        "management_methods": t(
            "Web; Hik-Central Pro; Hik-Partner Pro remote/cloud management; Super IP; DHCP client",
            "ei_1526_2026",
        ),
        "poe_standard": t("IEEE 802.3af/at", "ei_1526_2026"),
        "poe_ports": n(24, "ei_1526_2026"),
        "poe_budget_w": n(370, "ei_1526_2026"),
        "max_poe_per_port_w": n(30, "ei_1526_2026"),
        "vlan_count": n(32, "ei_1526_2026"),
        "l2_features": t(
            "IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; QoS; port mirroring",
            "ei_1526_2026",
        ),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1526_2026"),
        "acl_security": t("DHCP snooping; port isolation", "ei_1526_2026"),
        "max_power_consumption_w": n(400, "ei_1526_2026"),
        "dimensions_mm": t("440.0 x 220.8 x 44.0 mm (W x D x H)", "ei_1526_2026"),
        "operating_temperature_c": t("0 to 45 °C", "ei_1526_2026"),
    },
    "DS-3E1518P-EI/M": {
        **EI_M_COMMON,
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 2.5 A", "ei_m_1518"),
        "poe_ports": n(16, "ei_m_1518"),
        "poe_budget_w": n(130, "ei_m_1518"),
        "max_power_consumption_w": n(150, "ei_m_1518"),
    },
    "DS-3E1526P-EI/M": {
        **{
            code: (kind, value, "ei_m_1526")
            for code, (kind, value, _source) in EI_M_COMMON.items()
        },
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 4 A", "ei_m_1526"),
        "poe_ports": n(24, "ei_m_1526"),
        "poe_budget_w": n(230, "ei_m_1526"),
        "max_power_consumption_w": n(250, "ei_m_1526"),
    },
    "DS-3T2506P": {
        "switching_capacity_gbps": n(20, "industrial_2506"),
        "packet_forwarding_rate_mpps": n(14.88, "industrial_2506"),
        "mac_address_table": t("8K entries", "industrial_2506"),
        "power_supply": t("48-54 V DC, redundant dual inputs; power supply unit not included", "industrial_2506"),
        "fan_design": t("Fanless", "industrial_2506"),
        "management_methods": t("Web browser; CLI; Telnet; serial/RJ45 console; SSH; SNMP v1/v2c/v3; RMON; FTP/TFTP/SFTP", "industrial_2506"),
        "poe_configuration": t("PoE device detection and PoE power management", "industrial_2506"),
        "poe_standard": t("IEEE 802.3af/at PoE/PoE+", "industrial_2506"),
        "poe_ports": n(4, "industrial_2506"),
        "transmission_method": t("4 Gigabit copper PoE ports; 2 Gigabit SFP fiber ports; serial/RJ45 management console", "industrial_2506"),
        "vlan_count": n(256, "industrial_2506"),
        "l2_features": t("IEEE 802.1Q and port-based VLAN; GVRP; QinQ; private VLAN; IGMP/MLD snooping; QoS; port mirroring", "industrial_2506"),
        "stp_features": t("STP; RSTP; MSTP; EAPS/MEAPS; ERPS", "industrial_2506"),
        "acl_security": t("AAA/TACACS+/RADIUS; 802.1X and MAC authentication; DoS/ARP/ICMP attack prevention; IP-MAC binding; MAC filtering; storm control", "industrial_2506"),
        "max_power_consumption_w": n(120, "industrial_2506"),
        "dimensions_mm": t("110 x 42 x 105 mm", "industrial_2506"),
        "operating_temperature_c": t("-40 to 75 °C", "industrial_2506"),
    },
    "DS-3E1518P-SI": {
        "switching_capacity_gbps": n(56, "si_1518"),
        "packet_forwarding_rate_mpps": n(41.66, "si_1518"),
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 4 A", "si_1518"),
        "management_methods": t("Hik-Partner Pro remote management; system maintenance and remote upgrade", "si_1518"),
        "poe_standard": t("IEEE 802.3af/at", "si_1518"),
        "poe_ports": n(16, "si_1518"),
        "poe_budget_w": n(225, "si_1518"),
        "max_poe_per_port_w": n(30, "si_1518"),
        "vlan_count": n(4094, "si_1518"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; QoS; storm control", "si_1518"),
        "stp_features": t("IEEE 802.1D STP loop prevention", "si_1518"),
        "max_power_consumption_w": n(250, "si_1518"),
        "dimensions_mm": t("440 x 44 x 220.8 mm", "si_1518"),
        "operating_temperature_c": t("0 to 45 °C", "si_1518"),
    },
    "DS-3E1526P-SI": {
        "switching_capacity_gbps": n(52, "si_1526"),
        "packet_forwarding_rate_mpps": n(36.688, "si_1526"),
        "mac_address_table": t("8K entries", "si_1526"),
        "packet_buffer_mb": n(0.513, "si_1526"),
        "power_supply": t("100-240 V AC, 50/60 Hz, maximum 6.3 A", "si_1526_page"),
        "management_methods": t(
            "SNMP v1/v2c; Hikvision software-platform topology and health monitoring; remote upgrade, logs and network configuration",
            "si_1526",
        ),
        "poe_standard": t("IEEE 802.3af/at", "si_1526"),
        "poe_ports": n(24, "si_1526"),
        "poe_budget_w": n(370, "si_1526"),
        "max_poe_per_port_w": n(30, "si_1526"),
        "vlan_count": n(4094, "si_1526"),
        "l2_features": t(
            "Static link aggregation; port isolation; LLDP; QoS; port mirroring; storm control",
            "si_1526",
        ),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "si_1526"),
        "max_power_consumption_w": n(400, "si_1526_page"),
        "dimensions_mm": t("440 x 221 x 44 mm (W x D x H)", "si_1526_page"),
        "operating_temperature_c": t("0 to 45 °C", "si_1526_page"),
    },
    "DS-3E1506P-EI": {
        "switching_capacity_gbps": n(14, "ei_1506"),
        "packet_forwarding_rate_mpps": n(10.42, "ei_1506"),
        "power_supply": t("54 V DC, 1.2 A", "ei_1506"),
        "management_methods": t("Web; Hik-Partner Pro; Hik-Central Pro; SNMP v1/v2c; Super IP", "ei_1506"),
        "poe_standard": t("IEEE 802.3af/at", "ei_1506"),
        "poe_ports": n(4, "ei_1506"),
        "poe_budget_w": n(60, "ei_1506"),
        "max_poe_per_port_w": n(30, "ei_1506"),
        "vlan_count": n(32, "ei_1506"),
        "l2_features": t("IEEE 802.1Q; trunk/access modes; static link aggregation; port isolation; LLDP; port mirroring", "ei_1506"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP", "ei_1506"),
        "max_power_consumption_w": n(65, "ei_1506"),
        "dimensions_mm": t("121.1 x 27.6 x 83.1 mm", "ei_1506"),
        "operating_temperature_c": t("0 to 40 °C", "ei_1506"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified specifications for high-missingness Hikvision switches."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Hikvision").first()
        if not brand:
            raise CommandError("Brand 'Hikvision' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        documents = {}
        for key, meta in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=meta["url"],
                document_version=meta["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": meta.get("document_type", SourceDocument.DocumentType.DATASHEET),
                    "title": meta["title"],
                    "region": meta.get("region", "Global"),
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, value, source_key) in values.items():
                definition = definitions[code]
                source = documents[source_key]
                source_url = SOURCES[source_key]["url"]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": "4.1 Mbits" if code == "packet_buffer_mb" else str(value),
                    "source_url": source_url[:200],
                    "source_note": (
                        "Manually verified from the official model product page."
                        if SOURCES[source_key].get("document_type") == SourceDocument.DocumentType.PRODUCT_PAGE
                        else "Manually verified from the official model datasheet. Fields absent from the "
                        "datasheet, including jumbo-frame size and some fan/PoE limits, remain unknown."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                pages = "pp. 1-3" if source_key.startswith("ei_m") else "pp. 1-3"
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Official datasheet {pages} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {defaults['raw_value']}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
