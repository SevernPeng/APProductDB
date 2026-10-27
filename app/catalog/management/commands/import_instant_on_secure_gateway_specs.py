from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    na,
    t,
)


DATASHEET_URL = "https://instant-on.hpe.com/files/DS_HPE-NIO_Secure-Gateways_082025.pdf"


COMMON = {
    "vpn_protocols": t("IPsec site-to-site VPN; WireGuard client VPN"),
    "controller_management": t(
        "HPE Networking Instant On mobile app and web/cloud portal"
    ),
    "wan_load_balancing": b(
        True,
        "WAN failover and load balancing across two active WAN links",
    ),
    "firewall_features": t(
        "Hardware-accelerated firewall; IDS/IPS detection and prevention; threat event logging; "
        "application visibility; remote-access policies; TPM 2.0"
    ),
    "concurrent_sessions": n(16384, "Maximum accelerated TCP sessions: 16,384"),
    "operating_temperature_c": t("0 to 40 °C"),
}


PRODUCTS = {
    "SG1004": {
        "url": DATASHEET_URL,
        "page": "pp. 3-5, features and technical specifications, SG1004 column",
        "title": "HPE Networking Instant On Secure Gateways Data Sheet, August 2025",
        "values": {
            **COMMON,
            "wan_interfaces": t(
                "1 x 1GbE WAN; 1 x 1GbE WAN/LAN configurable as secondary WAN"
            ),
            "lan_interfaces": t(
                "2 x 1GbE LAN; 1 x 1GbE WAN/LAN configurable interface"
            ),
            "uplink_interfaces": t(
                "1 x 1GbE WAN; secondary 1GbE WAN available on the WAN/LAN port"
            ),
            "routing_throughput_mbps": n(
                980,
                "Routing performance: 980 Mbps (1518-byte packets, bidirectional, 500 firewall rules and 10 routes)",
            ),
            "vpn_throughput_mbps": n(
                930,
                "VPN performance: 930 Mbps (gateway-to-gateway, UDP, 1390-byte packets)",
            ),
            "vpn_tunnels": n(10, "Number of VPN tunnels supported: 10"),
            "usb_interfaces": na("Additional interfaces: none"),
            "max_power_consumption_w": n(12, "Maximum power rating: 12 W"),
            "dimensions_mm": t(
                "43.9 x 164.1 x 190.0 mm (official L x W x H order)"
            ),
        },
    },
    "SG2505P": {
        "url": DATASHEET_URL,
        "page": "pp. 3-5, features and technical specifications, SG2505P column",
        "title": "HPE Networking Instant On Secure Gateways Data Sheet, August 2025",
        "values": {
            **COMMON,
            "wan_interfaces": t(
                "1 x 2.5GbE WAN; 1 x 2.5GbE WAN/LAN and 1 x 1GbE WAN/LAN, with one configurable as secondary WAN"
            ),
            "lan_interfaces": t(
                "2 x 1GbE LAN; 1 x 2.5GbE and 1 x 1GbE WAN/LAN configurable interfaces"
            ),
            "uplink_interfaces": t(
                "1 x 2.5GbE WAN; secondary WAN configurable on one 2.5GbE or 1GbE WAN/LAN port"
            ),
            "routing_throughput_mbps": n(
                2400,
                "Routing performance: 2.4 Gbps (1518-byte packets, bidirectional, 500 firewall rules and 10 routes)",
            ),
            "vpn_throughput_mbps": n(
                2300,
                "VPN performance: 2.3 Gbps (gateway-to-gateway, UDP, 1390-byte packets)",
            ),
            "vpn_tunnels": n(25, "Number of VPN tunnels supported: 25"),
            "usb_interfaces": t("1 x USB-A 2.0"),
            "max_power_consumption_w": n(79.5, "Maximum power rating: 79.5 W"),
            "dimensions_mm": t(
                "43.9 x 309.6 x 234.2 mm (official L x W x H order)"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified HPE Networking Instant On secure gateway specifications."
    products = PRODUCTS
    document_version = "DS_HPE-NIO_Secure-Gateways_DP_082025; accessed 2026-10-23"
    brand_name = "Aruba /\nInstant On"
