from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "PFS4207-4GT-DP": {
        "url": "https://www.dahuasecurity.com/in/products/Transmission/PoE-Switches/Industrial-PoE-Switch/PFS4207-4GT-DP",
        "page": "Official product specifications and 2024-01-15 datasheet",
        "title": "Dahua PFS4207-4GT-DP official specifications",
        "values": {
            "ethernet_interfaces": t("5 x 10/100/1000 Mbps RJ45 ports, 4 with PoE; 2 x 1G SFP ports"),
            "console_interfaces": t("1 x console port"),
            "switching_capacity_gbps": n(14),
            "packet_forwarding_rate_mpps": n(10.42),
            "packet_buffer_mb": n(0.219, "1.75 Mbit, approximately 0.219 MB"),
            "mac_address_table": t("4K"),
            "jumbo_frame_bytes": n(9000),
            "l2_features": t("802.1Q VLAN; ERPS; static aggregation and LACP; port mirroring; multicast; flow control"),
            "stp_features": t("ERPS and loop protection"),
            "erps_support": b(True),
            "dhcp_features": t("DHCP client, server and snooping"),
            "acl_security": t("User management, HTTPS, SSH, SNMP v1/v2c/v3, ACL and 802.1X"),
            "management_methods": t("Web and SNMP v1/v2c/v3; configuration upload/download and system logs"),
            "poe_budget_w": n(120),
            "poe_configuration": t("Ports 1-2 up to 90 W; ports 3-5 up to 30 W; long-distance PoE and overload protection"),
            "max_power_consumption_w": n(120, "Full-load power consumption"),
            "power_supply": t("48 to 57 VDC; external supply sold separately"),
            "lightning_protection_kv": t("Common mode 6 kV; differential mode 4 kV"),
            "operating_temperature_c": t("-40 to 75 °C"),
            "dimensions_mm": t("94.4 x 53.5 x 135 mm"),
        },
    },
    "PFS3010-8ET-65": {
        "url": "https://www.dahuasecurity.com/uk/products/Transmission/PoE-Switches/Desktop-PoE-Switch/PFS3010-8ET-65",
        "page": "Official product specifications and 2020-07-08 datasheet",
        "title": "Dahua PFS3010-8ET-65 official specifications",
        "values": {
            "ethernet_interfaces": t("8 x 10/100 Mbps RJ45 PoE ports; 2 x 10/100 Mbps RJ45 uplink ports"),
            "uplink_interfaces": t("2 x 10/100 Mbps RJ45 uplink ports"),
            "switching_capacity_gbps": n(2),
            "packet_forwarding_rate_mpps": n(1.49),
            "mac_address_table": t("2K"),
            "jumbo_frame_bytes": n(2048),
            "poe_ports": n(8),
            "poe_budget_w": n(65),
            "max_poe_per_port_w": n(30),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "max_power_consumption_w": n(65, "Full-load power consumption"),
            "extend_mode": b(True, "Long-distance PoE transmission supported"),
            "poe_auto_recovery": b(True, "PoE watchdog supported"),
            "operating_temperature_c": t("-10 to 55 °C"),
            "dimensions_mm": t("242.5 x 122.9 x 35.0 mm"),
            "installation": t("Desktop"),
        },
    },
    "PFT1500": {
        "url": "https://www.dahuasecurity.com/in/products/Transmission/Accessories/PoE-Extender/PFT1500",
        "page": "Official V2.0 product specifications and 2021-11-18 datasheet",
        "title": "Dahua PFT1500 official specifications",
        "values": {
            "ethernet_interfaces": t("4 x 10/100 Mbps RJ45 PoE output ports; 1 x Gigabit RJ45 PoE input port"),
            "switching_capacity_gbps": n(2.8),
            "packet_forwarding_rate_mpps": n(2.08),
            "packet_buffer_mb": n(0.125, "1 Mbit"),
            "mac_address_table": t("4K"),
            "jumbo_frame_bytes": n(9000, "9K byte"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_ports": n(4),
            "poe_budget_w": n(90),
            "max_poe_per_port_w": n(90, "Port 1 up to 90 W; ports 2-4 up to 30 W"),
            "poe_standard": t("IEEE 802.3af / 802.3at / 802.3bt and Hi-PoE"),
            "max_power_consumption_w": n(90, "Full-load power consumption"),
            "extend_mode": b(True, "DIP-switch long-distance PoE mode up to 250 m"),
            "poe_auto_recovery": b(True, "PoE Watchdog"),
            "fanless": b(True),
            "operating_temperature_c": t("-30 to 65 °C"),
            "dimensions_mm": t("150 x 100 x 30 mm"),
            "installation": t("Desktop or DIN-rail mount"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Dahua switch and PoE-extender specifications."
    products = PRODUCTS
    document_version = "Dahua official product pages and latest linked datasheets; accessed 2026-10-16"
    brand_name = "Dahua"
