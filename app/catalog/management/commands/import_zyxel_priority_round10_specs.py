from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    Brand,
    Product,
    ProductSpec,
    ProductType,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
)


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


def na(reason="Not applicable"):
    return "not_applicable", reason


GS1005HP_URL = "https://www.zyxel.com/global/en/products/switch/gs1005hp/specifications"
GS1008HP_URL = "https://www.zyxel.com/global/en/products/switch/gs1008hp/specifications"
GS1100_SPECS_URL = (
    "https://www.zyxel.com/pl/pl/products/switch/gs1100-unmanaged-plus-series/specifications"
)
GS1100_FEATURES_URL = (
    "https://www.zyxel.com/pl/pl/products/switch/gs1100-unmanaged-plus-series/features"
)
MG108_URL = "https://www.zyxel.com/sites/zyxel/files/solution/Switch_Quick_Sales_Guide_2023.pdf"
NWA240BE_URL = "https://www.zyxel.com/global/en/products/wireless/nwa240be/specifications"
NWA130BE_URL = "https://www.zyxel.com/sk/sk/products/wireless/nwa130be/specifications"
WBE665S_URL = "https://www.zyxel.com/global/en/products/wireless/wbe665s/specifications"
WBE530_URL = "https://download.zyxel.com/WBE530/datasheet/WBE530_2.pdf"
WAC500H_URL = "https://download.zyxel.com/WAC500H/datasheet/WAC500H_8.pdf"
NWA110AX_URL = "https://download.zyxel.com/NWA110AX/datasheet/NWA110AX_10.pdf"
WAX510D_URL = "https://download.zyxel.com/WAX510D/datasheet/WAX510D_9.pdf"
WAX300H_URL = "https://download.zyxel.com/WAX300H/datasheet/WAX300H_4.pdf"
NWA210AXV2_URL = "https://www.zyxel.com/nl/nl/products/wireless/nwa210axv2/specifications"
WBE660S_URL = "https://www.zyxel.com/global/en/products/wireless/wbe660s/specifications"
NWA90BE_URL = "https://www.zyxel.com/global/en/products/wireless/nwa90be/specifications"
NWA50BE_URL = "https://www.zyxel.com/global/en/products/wireless/nwa50be/specifications"
NWA90AX_URL = "https://www.zyxel.com/global/en/products/wireless/nwa90ax/specifications"
NWA50AX_URL = "https://www.zyxel.com/global/en/products/wireless/nwa50ax/specifications"
NWA90AX_PRO_URL = "https://www.zyxel.com/global/en/products/wireless/nwa90ax-pro/specifications"
NWA50AX_PRO_URL = "https://www.zyxel.com/global/en/products/wireless/nwa50ax-pro/specifications"
NWA55BE_URL = "https://www.zyxel.com/global/en/products/wireless/nwa55be/specifications"
NWA55AXE_URL = "https://www.zyxel.com/in/en-in/products/wireless/nwa55axe/specifications"
NWA55AX_PRO_URL = "https://www.zyxel.com/tr/tr/products/wireless/nwa55ax-pro/specifications"
SWITCH_QSG_2025_URL = (
    "https://www.zyxel.com/sites/zyxel/files/library/assets/tech-library/quick-sales-guide/"
    "qsg_switch_2025.pdf"
)
MC1000_SFP_A_URL = "https://www.zyxel.com/in/en-in/products/switch/mc1000-sfp-a/specification"


GS1100_FEATURE_NOTE = (
    "The current official Unmanaged Plus series feature page confirms IEEE 802.3x flow control, "
    "IEEE 802.1p CoS, 802.1Q VLAN, VLAN trunking, loop prevention and port isolation "
    f"({GS1100_FEATURES_URL})."
)


PRODUCTS = {
    "GS1005HP": {
        "source": "gs1005hp",
        "values": {
            "power_supply": t("External AC-to-DC adapter; 100-240 V AC, 50/60 Hz input"),
            "flow_control": t("IEEE 802.3x flow control"),
            "installation": t("Desktop or wall mount"),
            "max_power_consumption_w": n(71.99),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "GS1008HP": {
        "source": "gs1008hp",
        "values": {
            "power_supply": t("External AC-to-DC adapter; 100-240 V AC, 50/60 Hz input"),
            "flow_control": t("IEEE 802.3x flow control"),
            "installation": t("Desktop or wall mount"),
            "max_power_consumption_w": n(78.69),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "GS1100-16": {
        "source": "gs1100",
        "values": {
            "ethernet_interfaces": t("16 x 10/100/1000 Mbps RJ45"),
            "management_type": t("Unmanaged Plus with web-based management"),
            "mac_address_table": t("16K entries"),
            "packet_buffer_mb": n(1),
            "jumbo_frame_bytes": n(12288),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS"),
            "port_isolation": b(),
            "loop_prevention": b(),
            "vlan_support": t("802.1Q VLAN and VLAN trunking"),
            "installation": t("Rack or wall mount"),
            "max_power_consumption_w": n(8.43),
            "dimensions_mm": t("165 x 118 x 39 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "GS1100-24E": {
        "source": "gs1100",
        "values": {
            "ethernet_interfaces": t("24 x 10/100/1000 Mbps RJ45"),
            "management_type": t("Unmanaged Plus with web-based management"),
            "mac_address_table": t("16K entries"),
            "packet_buffer_mb": n(1),
            "jumbo_frame_bytes": n(12288),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS"),
            "port_isolation": b(),
            "loop_prevention": b(),
            "vlan_support": t("802.1Q VLAN and VLAN trunking"),
            "installation": t("Rack or wall mount"),
            "max_power_consumption_w": n(13.75),
            "dimensions_mm": t("225 x 143.5 x 39 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "MG-108": {
        "source": "mg108",
        "values": {
            "installation": t("Desktop or wall mount"),
            "switching_capacity_gbps": n(40),
            "flow_control": t("IEEE 802.3x flow control"),
            "dimensions_mm": t("240 x 106 x 26 mm"),
        },
    },
    "NWA240BE": {
        "source": "nwa240be",
        "values": {
            "max_channel_width_mhz": n(320),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO"),
            "mimo_6g": t("2x2 MU-MIMO"),
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 5 dBi at 5 GHz; 5 dBi at 6 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(28),
            "dimensions_mm": t("270 x 150 x 47 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA130BE": {
        "source": "nwa130be",
        "values": {
            "max_channel_width_mhz": n(320),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "mimo_6g": t("2x2 MU-MIMO"),
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 4 dBi at 5 GHz; 4 dBi at 6 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(24),
            "dimensions_mm": t("250 x 160 x 47 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "WBE665S": {
        "source": "wbe665s",
        "values": {
            "max_channel_width_mhz": n(320),
            "mimo_2g": t("4x4 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO"),
            "mimo_6g": t("4x4 MU-MIMO"),
            "antenna_gain_dbi": t("5 dBi at 2.4 GHz; 6 dBi at 5 GHz; 5 dBi at 6 GHz"),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "max_power_consumption_w": n(40.64),
            "dimensions_mm": t("410 x 410 x 110 mm"),
            "operating_temperature_c": t("-40 to 70 °C"),
        },
    },
    "WBE530": {
        "source": "wbe530",
        "values": {
            "max_channel_width_mhz": n(320),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "mimo_6g": t("2x2 MU-MIMO"),
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 4 dBi at 5 GHz; 4 dBi at 6 GHz"),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "max_power_consumption_w": n(24),
            "dimensions_mm": t("250 x 160 x 47 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "WAC500H": {
        "source": "wac500h",
        "values": {
            "ethernet_interfaces": t(
                "1 x Gigabit Ethernet uplink; 2 x Gigabit Ethernet downlink, including one PoE PSE"
            ),
            "poe_output": t("One downlink PoE PSE port; 7 W available with 802.3at input"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_ssids": n(64),
            "max_power_consumption_w": n(18),
            "dimensions_mm": t("173 x 97 x 29 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA110AX": {
        "source": "nwa110ax",
        "values": {
            "max_channel_width_mhz": n(80),
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps LAN"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(17),
            "dimensions_mm": t("180 x 180 x 39 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "WAX510D": {
        "source": "wax510d",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps LAN"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "max_power_consumption_w": n(17),
            "dimensions_mm": t("180 x 180 x 39 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "WAX300H": {
        "source": "wax300h",
        "values": {
            "ethernet_interfaces": t(
                "1 x Gigabit Ethernet 802.3at uplink; 3 x Gigabit Ethernet downlink, including one PoE PSE"
            ),
            "poe_output": t("One downlink 802.3at PoE PSE port; 5 W available"),
            "max_ssids": n(64),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "max_power_consumption_w": n(19),
            "dimensions_mm": t("173 x 97 x 29 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA210AXv2": {
        "source": "nwa210axv2",
        "values": {
            "mimo_2g": t("2x2 MU-MIMO"),
            "antenna_gain_dbi": t("1.49 dBi at 2.4 GHz; 2.78 dBi at 5 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(21.5),
            "dimensions_mm": t("250 x 160 x 47 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "WBE660S": {
        "source": "wbe660s",
        "values": {
            "mimo_6g": t("4x4 MU-MIMO"),
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 5 dBi at 5 GHz; 5 dBi at 6 GHz"),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "max_power_consumption_w": n(41),
            "dimensions_mm": t("310 x 178 x 56 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "NWA90BE": {
        "source": "nwa90be",
        "values": {
            "antenna_gain_dbi": t("2 dBi at 2.4 GHz; 3 dBi at 5 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(16),
            "dimensions_mm": t("150 x 150 x 35 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA50BE": {
        "source": "nwa50be",
        "values": {
            "antenna_gain_dbi": t("2 dBi at 2.4 GHz; 3 dBi at 5 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(16),
            "dimensions_mm": t("150 x 150 x 35 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA90AX": {
        "source": "nwa90ax",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps LAN"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(16),
            "dimensions_mm": t("140 x 140 x 37.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA50AX": {
        "source": "nwa50ax",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps LAN"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(16),
            "dimensions_mm": t("140 x 140 x 37.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA90AX PRO": {
        "source": "nwa90ax_pro",
        "values": {
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(20.5),
            "dimensions_mm": t("140 x 140 x 37.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA50AX PRO": {
        "source": "nwa50ax_pro",
        "values": {
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(20.5),
            "dimensions_mm": t("140 x 140 x 37.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "NWA55BE": {
        "source": "nwa55be",
        "values": {
            "antenna_gain_dbi": t("2 dBi at 2.4 GHz; 3 dBi at 5 GHz"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(24),
            "dimensions_mm": t("308 x 136.4 x 49.6 mm"),
            "operating_temperature_c": t("-25 to 65 °C"),
        },
    },
    "NWA55AXE": {
        "source": "nwa55axe",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps LAN"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(16),
            "dimensions_mm": t("308 x 136.4 x 49.6 mm"),
            "operating_temperature_c": t("-20 to 60 °C"),
        },
    },
    "NWA55AX Pro": {
        "source": "nwa55ax_pro",
        "values": {
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 4 dBi at 5 GHz"),
            "wireless_range": t("Wireless bridge for short-distance links up to around 100 m"),
            "centralized_management": t("Nebula cloud or standalone"),
            "max_power_consumption_w": n(12),
            "dimensions_mm": t("180 x 99 x 35.9 mm"),
            "operating_temperature_c": t("-30 to 50 °C"),
        },
    },
    "GS1200-5": {
        "source": "switch_qsg_2025",
        "values": {"packet_forwarding_rate_mpps": n(7.44)},
    },
    "GS1200-8": {
        "source": "switch_qsg_2025",
        "values": {"packet_forwarding_rate_mpps": n(11.9)},
    },
    "GS1200-5HP": {
        "source": "switch_qsg_2025",
        "values": {"packet_forwarding_rate_mpps": n(7.44)},
    },
    "GS1350-6HP": {
        "source": "switch_qsg_2025",
        "values": {"jumbo_frame_bytes": n(9216)},
    },
    "GS1350-12HP": {
        "source": "switch_qsg_2025",
        "values": {"jumbo_frame_bytes": n(9216)},
    },
    "GS1350-18HP": {
        "source": "switch_qsg_2025",
        "values": {"jumbo_frame_bytes": n(9216)},
    },
    "GS1350-26HP": {
        "source": "switch_qsg_2025",
        "values": {"jumbo_frame_bytes": n(9216)},
    },
    "PoE12-30W": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_connector_type": t("RJ-45"),
            "accessory_compatibility": t(
                "100M/1G/2.5G Ethernet powered devices; IEEE 802.3af PoE and 802.3at PoE+"
            ),
            "dimensions_mm": t("140 x 45.5 x 30 mm"),
        },
    },
    "PoE12-60W": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_connector_type": t("RJ-45"),
            "accessory_compatibility": t(
                "100M/1G/2.5G/5G/10G Ethernet powered devices; IEEE 802.3af/at/bt up to 60 W"
            ),
            "dimensions_mm": t("140 x 65 x 38.5 mm"),
        },
    },
    "PoE12-90W": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_connector_type": t("RJ-45"),
            "accessory_compatibility": t(
                "100M/1G/2.5G/5G/10G Ethernet powered devices; IEEE 802.3af/at/bt up to 90 W"
            ),
        },
    },
    "MC1000-SFP-A": {
        "source": "mc1000_sfp_a",
        "values": {
            "accessory_fiber_mode": t("Depends on installed SFP transceiver"),
            "accessory_max_distance_km": n(80),
            "accessory_input_power": t("External 5 V DC / 1 A adapter"),
            "accessory_compatibility": t("1000BASE-X SFP transceivers"),
            "dimensions_mm": t("71 x 94 x 26 mm"),
        },
    },
    "SFP-1000T": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_connector_type": t("RJ-45"),
            "accessory_wavelength_nm": na("Not applicable to copper transceiver"),
            "accessory_fiber_mode": na("Not applicable to copper transceiver"),
            "accessory_max_distance_km": n(0.1),
            "accessory_compatibility": t("SFP MSA-compliant Gigabit SFP ports; RJ-45 copper link"),
        },
    },
    "SFP-SX-D": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_wavelength_nm": n(850),
            "accessory_max_distance_km": n(0.55),
            "accessory_compatibility": t("SFP MSA-compliant Gigabit SFP ports"),
        },
    },
    "SFP10G-T": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP+"),
            "accessory_connector_type": t("RJ-45"),
            "accessory_wavelength_nm": na("Not applicable to copper transceiver"),
            "accessory_fiber_mode": na("Not applicable to copper transceiver"),
            "accessory_max_distance_km": n(0.03),
            "accessory_compatibility": t("SFP+ ports; Cat 6a/7 copper cable up to 30 m"),
        },
    },
    "SFP10G-SR": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP+"),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_compatibility": t("SFP MSA-compliant 10 Gigabit SFP+ ports"),
        },
    },
    "SFP10G-LR": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP+"),
            "accessory_wavelength_nm": n(1310),
            "accessory_compatibility": t("SFP MSA-compliant 10 Gigabit SFP+ ports"),
        },
    },
    "SFP25G-SR": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP28"),
            "accessory_data_rate_gbps": n(25),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(0.1),
            "accessory_compatibility": t("SFP MSA-compliant 25 Gigabit SFP28 ports"),
        },
    },
    "SFP25G-LR": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP28"),
            "accessory_data_rate_gbps": n(25),
            "accessory_wavelength_nm": n(1310),
            "accessory_fiber_mode": t("Single-mode"),
            "accessory_max_distance_km": n(10),
            "accessory_compatibility": t("SFP MSA-compliant 25 Gigabit SFP28 ports"),
        },
    },
    "QSFP100G-SR4": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("QSFP28"),
            "accessory_connector_type": t("MPO12"),
            "accessory_data_rate_gbps": n(100),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(0.1),
            "accessory_compatibility": t("100 Gigabit QSFP28 ports"),
        },
    },
    "DAC10G-1M": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP+"),
            "accessory_compatibility": t("10 Gigabit SFP+ ports; SFP+ to SFP+ direct-attach cable"),
        },
    },
    "DAC10G-3M": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_compatibility": t("10 Gigabit SFP+ ports; SFP+ to SFP+ direct-attach cable"),
        },
    },
    "DAC25G-1M": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("SFP28"),
            "accessory_data_rate_gbps": n(25),
            "accessory_compatibility": t("25 Gigabit SFP28 ports; SFP28 to SFP28 direct-attach cable"),
        },
    },
    "DAC100G-1M": {
        "source": "switch_qsg_2025",
        "values": {
            "accessory_interface_type": t("QSFP28"),
            "accessory_data_rate_gbps": n(100),
            "accessory_compatibility": t("100 Gigabit QSFP28 ports; QSFP28 to QSFP28 direct-attach cable"),
        },
    },
}


SOURCES = {
    "gs1005hp": {
        "url": GS1005HP_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel GS1005HP Specifications",
        "location": "Hardware, system, physical and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "gs1008hp": {
        "url": GS1008HP_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel GS1008HP Specifications",
        "location": "Hardware, system, physical and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "gs1100": {
        "url": GS1100_SPECS_URL,
        "version": "Current official Unmanaged Plus series pages, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel GS1100 Unmanaged Plus Series Specifications",
        "location": "Exact-model specification columns and series software feature list",
        "note": (
            "Manually verified from Zyxel's current official exact-model specification table. "
            + GS1100_FEATURE_NOTE
        ),
    },
    "mg108": {
        "url": MG108_URL,
        "version": "Official 2023 Switch Quick Sales Guide, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel Switch Quick Sales Guide 2023",
        "location": "MG-105/MG-108 feature matrix",
        "note": (
            "Manually verified from Zyxel's official switch guide; the current official MG-108 "
            "store page independently confirms 40 Gbps switching capacity."
        ),
    },
    "nwa240be": {
        "url": NWA240BE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA240BE Specifications",
        "location": "Wireless, RF, management, physical and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa130be": {
        "url": NWA130BE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA130BE Specifications",
        "location": "Wireless, RF, management, physical and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "wbe665s": {
        "url": WBE665S_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel WBE665S Specifications",
        "location": "Wireless, RF, management, physical and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "wbe530": {
        "url": WBE530_URL,
        "version": "Official datasheet version 2, released 2025-12-05",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel WBE530 Datasheet",
        "location": "Wireless/RF specifications p. 3 and management/physical/environmental specifications p. 4",
        "note": (
            "Manually verified from Zyxel's latest official WBE530 datasheet version 2. "
            "The official 320 MHz bandwidth replaces the prior 80 MHz database value."
        ),
    },
    "wac500h": {
        "url": WAC500H_URL,
        "version": "Official datasheet version 8, released 2024-04-08",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel WAC500H Datasheet",
        "location": "Wireless/management specifications p. 4 and physical/interface/environmental specifications p. 5",
        "note": (
            "Manually verified from Zyxel's latest official exact-model datasheet version 8. "
            "The 64 SSID-profile value was cross-checked in the official V6.70 user guide."
        ),
    },
    "nwa110ax": {
        "url": NWA110AX_URL,
        "version": "Official datasheet version 10, released 2024-04-08",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel NWA110AX Datasheet",
        "location": "Wireless/RF/management specifications p. 3 and physical/interface/environmental specifications p. 4",
        "note": "Manually verified from Zyxel's latest official exact-model datasheet version 10.",
    },
    "wax510d": {
        "url": WAX510D_URL,
        "version": "Official datasheet version 9, released 2024-04-08",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel WAX510D Datasheet",
        "location": "Wireless/RF specifications p. 4 and management/physical/interface/environmental specifications p. 5",
        "note": "Manually verified from Zyxel's latest official exact-model datasheet version 9.",
    },
    "wax300h": {
        "url": WAX300H_URL,
        "version": "Official datasheet version 4, released 2024-04-08",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel WAX300H Datasheet",
        "location": "Wireless/management specifications p. 4 and physical/interface/environmental specifications p. 5",
        "note": (
            "Manually verified from Zyxel's latest official exact-model datasheet version 4. "
            "The 64 SSID-profile value was cross-checked in the current official V7.12 user guide."
        ),
    },
    "nwa210axv2": {
        "url": NWA210AXV2_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA210AXv2 Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "wbe660s": {
        "url": WBE660S_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel WBE660S Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa90be": {
        "url": NWA90BE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA90BE Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa50be": {
        "url": NWA50BE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA50BE Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa90ax": {
        "url": NWA90AX_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA90AX Specifications",
        "location": "Management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa50ax": {
        "url": NWA50AX_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA50AX Specifications",
        "location": "Management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa90ax_pro": {
        "url": NWA90AX_PRO_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA90AX PRO Specifications",
        "location": "Management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa50ax_pro": {
        "url": NWA50AX_PRO_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA50AX PRO Specifications",
        "location": "Management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa55be": {
        "url": NWA55BE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA55BE Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa55axe": {
        "url": NWA55AXE_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA55AXE Specifications",
        "location": "RF, management, physical, interface and environmental specifications",
        "note": "Manually verified from Zyxel's current official exact-model specifications page.",
    },
    "nwa55ax_pro": {
        "url": NWA55AX_PRO_URL,
        "version": "Current official specifications and FAQ pages, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel NWA55AX PRO Specifications",
        "location": "RF, management, physical, interface and environmental specifications; official FAQ for range",
        "note": (
            "Manually verified from Zyxel's current official exact-model specifications page and "
            "official FAQ. The current specifications list 12 W power draw; the FAQ's older 21 W "
            "statement was not used."
        ),
    },
    "switch_qsg_2025": {
        "url": SWITCH_QSG_2025_URL,
        "version": "Official 2025 Switch Quick Sales Guide, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel Switch Quick Sales Guide 2025",
        "location": "Switch matrices pp. 22-24 and accessories pp. 26-29",
        "note": (
            "Manually verified from Zyxel's official 2025 switch guide. Copper transceiver optical "
            "fields are marked not applicable; transmission distances use the guide's stated maximums."
        ),
    },
    "mc1000_sfp_a": {
        "url": MC1000_SFP_A_URL,
        "version": "Current official specification page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel MC1000-SFP-A Specification",
        "location": "Hardware, physical, power and environmental specifications",
        "note": (
            "Manually verified from Zyxel's current official exact-model specification page. "
            "Maximum fiber reach depends on the installed SFP transceiver."
        ),
    },
}


RAW_VALUES = {
    ("GS1005HP", "max_power_consumption_w"): "Max. power consumption: 71.99 watt",
    ("GS1008HP", "max_power_consumption_w"): "Max. power consumption: 78.69 watt",
    ("GS1100-16", "packet_buffer_mb"): "1MB",
    ("GS1100-16", "jumbo_frame_bytes"): "12KB",
    ("GS1100-24E", "packet_buffer_mb"): "1MB",
    ("GS1100-24E", "jumbo_frame_bytes"): "12KB",
    ("WBE530", "max_channel_width_mhz"): "20-, 40-, 80-, 160-, 240- and 320-MHz",
    ("MG-108", "switching_capacity_gbps"): "Switching capacity: 40 Gbps",
    ("GS1350-6HP", "jumbo_frame_bytes"): "Jumbo frame: 9K bytes",
    ("GS1350-12HP", "jumbo_frame_bytes"): "Jumbo frame: 9K bytes",
    ("GS1350-18HP", "jumbo_frame_bytes"): "Jumbo frame: 9K bytes",
    ("GS1350-26HP", "jumbo_frame_bytes"): "Jumbo frame: 9K bytes",
    ("PoE12-30W", "dimensions_mm"): "140 x 45.5 x 30 mm",
    ("PoE12-60W", "dimensions_mm"): "140 x 65 x 38.5 mm",
    ("SFP25G-SR", "accessory_max_distance_km"): "OM4: 0.1 km; OM3: 0.07 km",
    ("QSFP100G-SR4", "accessory_max_distance_km"): "OM4: 0.1 km; OM3: 0.07 km",
}


PRODUCT_TYPES = {
    "GS1005HP": "unmanaged_poe",
    "GS1008HP": "unmanaged_poe",
    "MG-108": "unmanaged_non_poe",
    "GS1100-16": "easy_smart_non_poe",
}


class Command(BaseCommand):
    help = "Import manually verified Zyxel priority specifications (round 10)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Zyxel").first()
        if not brand:
            raise CommandError("Missing brand: Zyxel")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, row in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": row["type"],
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = type_updates = 0
        per_model = []
        missing_models = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            if type_code := PRODUCT_TYPES.get(model):
                target_type = ProductType.objects.get(category=product.category, code=type_code)
                if product.product_type_id != target_type.id:
                    product.product_type = target_type
                    product.save(update_fields=["product_type"])
                    type_updates += 1
            source = documents[item["source"]]
            source_meta = SOURCES[item["source"]]
            model_new = model_corrected = 0
            for code, (kind, value) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had_value = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                was_not_applicable = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.NOT_APPLICABLE
                )
                old_value = None
                if had_value:
                    old_value = (
                        existing.value_text
                        if existing.value_text
                        else existing.value_number
                        if existing.value_number is not None
                        else existing.value_boolean
                    )

                raw_value = RAW_VALUES.get((model, code), str(value))
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw_value,
                    "source_url": source.url[:200],
                    "source_note": source_meta["note"],
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                elif kind == "not_applicable":
                    defaults["value_status"] = ProductSpec.ValueStatus.NOT_APPLICABLE
                    defaults["normalized_value"] = ""
                    new_value = None
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)

                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if kind == "not_applicable" and was_not_applicable:
                    unchanged += 1
                elif kind == "not_applicable":
                    corrected += 1
                    model_corrected += 1
                elif not had_value:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1

                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{source_meta['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw_value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} type_updates={type_updates} "
                f"models={len(PRODUCTS)-len(missing_models)}"
            )
        )
        self.stdout.write("; ".join(per_model))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
