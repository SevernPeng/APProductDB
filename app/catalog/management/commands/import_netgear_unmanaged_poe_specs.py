from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_FLEX = "https://www.downloads.netgear.com/files/GDC/Unmanaged_Switches/GS105Pv3_GS105PPv3_GS108LP_GS108PP_GS116LP_GS116PP_DS.pdf"
URL_300 = "https://www.downloads.netgear.com/files/netgear/pdfs/300-Series-Unmanaged-PoE-DS.pdf"
URL_OLD_300 = "https://www.netgear.com/images/datasheet/switches/300-Series_PoE_Gigabit_DS.pdf"


PRODUCTS = {
    "GS108LP": {
        "url": URL_FLEX,
        "page": "pp. 1-5, hardware and technical specification tables",
        "title": "NETGEAR GS105P/GS105PP/GS108LP/GS108PP/GS116LP/GS116PP Data Sheet (17 April 2025)",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45; all 8 ports support PoE/PoE+"),
            "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
            "poe_ports": n(8),
            "poe_budget_w": n(60, "60 W standard; upgradeable to 83 W or 123 W with optional PSU"),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n("67.5"),
            "switching_capacity_gbps": n(16),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n("0.188", "Buffer size: 192 KB"),
            "jumbo_frame_bytes": n(10000),
            "management_type": t("Unmanaged, plug-and-play"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("DSCP and IEEE 802.1p CoS; weighted fair queues"),
            "fanless": b(True, "Acoustic noise: 0 dBA (fanless)"),
            "installation": t("Desktop, wall mount, or standard 19-inch rack mount"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("236 x 102 x 27 mm (W x D x H)"),
        },
    },
    "GS305P": {
        "url": URL_300,
        "page": "pp. 4-5, GS305Pv3 technical specifications",
        "title": "NETGEAR 300 Series Gigabit Unmanaged Essentials PoE Switches Data Sheet",
        "values": {
            "ethernet_interfaces": t("5 x 10/100/1000BASE-T RJ45; ports 1-4 PoE+"),
            "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
            "poe_ports": n(4),
            "poe_budget_w": n(63),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n("66.78"),
            "switching_capacity_gbps": n(10),
            "mac_address_table": t("2K entries"),
            "packet_buffer_mb": n("0.125", "128 KB"),
            "jumbo_frame_bytes": n(9216),
            "management_type": t("Unmanaged, plug-and-play"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS and DSCP"),
            "fanless": b(True),
            "installation": t("Desktop or wall mount"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("158 x 101 x 27 mm (W x D x H)"),
        },
    },
    "GS308P": {
        "url": URL_OLD_300,
        "page": "pp. 2-4, GS308P column in technical specification table",
        "title": "NETGEAR 300 Series SOHO Gigabit Ethernet Unmanaged Switches with PoE Data Sheet",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45; ports 1-4 PoE"),
            "poe_standard": t("IEEE 802.3af PoE"),
            "poe_ports": n(4),
            "poe_budget_w": n(53),
            "max_poe_per_port_w": n("15.4"),
            "max_power_consumption_w": n(60),
            "switching_capacity_gbps": n(16),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n("0.188", "192 KB"),
            "jumbo_frame_bytes": n(9720),
            "management_type": t("Unmanaged, plug-and-play"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS"),
            "fanless": b(True),
            "installation": t("Desktop or wall mount"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("158 x 101 x 29 mm (W x D x H)"),
        },
    },
    "GS316P": {
        "url": URL_300,
        "page": "pp. 3-5, GS316P technical specifications",
        "title": "NETGEAR 300 Series Gigabit Unmanaged Essentials PoE Switches Data Sheet",
        "values": {
            "ethernet_interfaces": t("16 x 10/100/1000BASE-T RJ45; all 16 ports PoE+"),
            "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
            "poe_ports": n(16),
            "poe_budget_w": n(115, "115 W standard; FlexPoE upgradeable to 183 W"),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n("127.9"),
            "switching_capacity_gbps": n(32),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n(1),
            "jumbo_frame_bytes": n(9216),
            "management_type": t("Unmanaged, plug-and-play"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS and DSCP"),
            "fanless": b(True),
            "installation": t("Desktop or wall mount"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("286 x 102 x 27 mm (W x D x H)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR unmanaged PoE switch specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR unmanaged PoE switch datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
