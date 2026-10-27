from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL = "https://www.cisco.com/c/en/us/products/collateral/security/meraki-cloud-managed-security-appliances/mx-family-ds.html"
URL_MX67 = "https://documentation.meraki.com/MX/MX_Overviews_and_Specifications/MX67_and_MX68_Datasheet"


COMMON = {
    "controller_management": t(
        "Cisco Meraki Dashboard cloud management; zero-touch deployment, automatic firmware/security updates, "
        "templates, role-based administration, monitoring, NetFlow and syslog"
    ),
    "firewall_features": t(
        "Stateful NGFW, Layer 7 application firewall, 1:1 NAT, DMZ, identity-based policies, content filtering, "
        "Snort IDS/IPS, Cisco AMP, malware analytics and GeoIP rules (features vary by license)"
    ),
    "sd_wan": t(
        "Meraki SD-WAN with Auto VPN, dual-active VPN, policy-based routing, dynamic path selection, "
        "WAN health analytics and automatic Layer 3 failover"
    ),
    "vpn_protocols": t("Meraki Auto VPN site-to-site IPsec; client IPsec/L2TP VPN; Cisco Secure Client VPN"),
    "wan_load_balancing": b(True, "Multiple uplinks with load balancing, dynamic path selection and failover"),
}


def values(**kwargs):
    return {**COMMON, **kwargs}


PRODUCTS = {
    "MX67": {
        "url": URL,
        "page": "Desktop and all-in-one models and MX specifications, updated 2026-09-01",
        "title": "Cisco Meraki MX Family Data Sheet",
        "values": values(
            dimensions_mm=t("239 x 130 x 27 mm (W x D x H)"),
            lan_interfaces=t("3 x dedicated 1GbE RJ-45 LAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
            max_power_consumption_w=n(14, "Published power load: 5 W idle, 14 W maximum"),
            operating_temperature_c=t("0 to 45 °C"),
            routing_throughput_mbps=n(700, "Published firewall throughput; routing-performance field retains the original metric name in evidence"),
            uplink_interfaces=t("1 x dedicated 1GbE RJ-45 WAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
            usb_interfaces=t("1 x USB 3.0 for external 3G/4G modem (legacy cellular failover support)"),
            vpn_throughput_mbps=n(400, "Maximum site-to-site VPN throughput"),
            vpn_tunnels=n(50, "Maximum site-to-site VPN tunnels in lab testing"),
            wan_interfaces=t("1 x dedicated 1GbE RJ-45 WAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
        ),
    },
    "MX67W": {
        "url": URL_MX67,
        "page": "Throughput, interface, wireless and physical specifications; updated 2026-05-29",
        "title": "Cisco Meraki MX67 and MX68 Data Sheet",
        "values": values(
            dimensions_mm=t("239 x 164 x 27 mm (W x D x H)"),
            lan_interfaces=t("3 x dedicated 1GbE RJ-45 LAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
            max_power_consumption_w=n(23, "Published power load: 15 W idle, 23 W maximum"),
            operating_temperature_c=t("0 to 45 °C"),
            router_supported_bands=t("2.4 GHz and 5 GHz"),
            router_wifi_standard=t("IEEE 802.11a/b/g/n/ac Wave 2, 2x2 MU-MIMO"),
            router_wireless_rate_mbps=n(1300, "Published maximum aggregate wireless data rate"),
            routing_throughput_mbps=n(700, "Published stateful firewall throughput; routing-performance field retains the original metric name in evidence"),
            uplink_interfaces=t("1 x dedicated 1GbE RJ-45 WAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
            usb_interfaces=t("1 x USB 3.0 for external 3G/4G modem (legacy cellular failover support)"),
            vpn_throughput_mbps=n(400, "Maximum site-to-site VPN throughput"),
            vpn_tunnels=n(50, "Maximum site-to-site VPN tunnels in lab testing"),
            wan_interfaces=t("1 x dedicated 1GbE RJ-45 WAN; 1 x convertible 1GbE LAN/WAN RJ-45"),
        ),
    },
    "MX85": {
        "url": URL,
        "page": "Rack-mount models and MX specifications, updated 2026-09-01",
        "title": "Cisco Meraki MX Family Data Sheet",
        "values": values(
            dimensions_mm=t("484.6 x 250 x 43.8 mm (W x D x H), 1RU"),
            lan_interfaces=t("8 x 1GbE RJ-45 and 2 x 1GbE SFP fixed LAN interfaces"),
            max_power_consumption_w=n(55, "Published power load: 12 W idle, 55 W maximum"),
            operating_temperature_c=t("0 to 40 °C"),
            routing_throughput_mbps=n(1000, "Published firewall throughput; routing-performance field retains the original metric name in evidence"),
            uplink_interfaces=t("2 x 1GbE SFP and 2 x 1GbE RJ-45 dedicated WAN interfaces"),
            vpn_throughput_mbps=n(1000, "Maximum site-to-site VPN throughput"),
            vpn_tunnels=n(200, "Maximum site-to-site VPN tunnels in lab testing"),
            wan_interfaces=t("2 x 1GbE SFP and 2 x 1GbE RJ-45 dedicated WAN interfaces"),
        ),
    },
    "C8111-G2-MX": {
        "url": URL,
        "page": "Cisco 8000 desktop models and MX specifications, updated 2026-09-01",
        "title": "Cisco Meraki MX Family Data Sheet",
        "values": values(
            dimensions_mm=t("273 x 143 x 34 mm (W x D x H)"),
            lan_interfaces=t("4 x 1GbE RJ-45 fixed LAN interfaces; 1 x convertible 1GbE RJ-45"),
            max_power_consumption_w=n(22, "Published maximum system power excluding PoE output load"),
            operating_temperature_c=t("0 to 45 °C"),
            router_poe_budget_w=n(45, "Published LAN PoE power budget"),
            router_poe_ports=n(1, "One fixed LAN port supports PoE output; one WAN port separately supports PoE"),
            routing_throughput_mbps=n(2000, "Published firewall throughput; routing-performance field retains the original metric name in evidence"),
            uplink_interfaces=t("2 x 2.5GbE Multigigabit RJ-45 WAN (one PoE+); 1 x convertible 1GbE RJ-45"),
            vpn_throughput_mbps=n(1200, "Maximum site-to-site VPN throughput"),
            vpn_tunnels=n(150, "Maximum site-to-site VPN tunnels in lab testing"),
            wan_interfaces=t("2 x 2.5GbE Multigigabit RJ-45 WAN (one PoE+); 1 x convertible 1GbE RJ-45"),
        ),
    },
    "C8355-G2-MX": {
        "url": URL,
        "page": "Cisco 8000 rack-mount models and MX specifications, updated 2026-09-01",
        "title": "Cisco Meraki MX Family Data Sheet",
        "values": values(
            dimensions_mm=t("444.5 x 291.84 x 43.9 mm (W x D x H), 1RU"),
            lan_interfaces=t("4 x 5GbE Multigigabit RJ-45 and 2 x 1GbE RJ-45 fixed LAN; 2 x convertible 10GbE"),
            operating_temperature_c=t("0 to 40 °C at sea level"),
            router_poe_budget_w=n(120, "Four UPOE+ ports share a published 120 W PoE budget"),
            router_poe_ports=n(4, "Four 5GbE LAN ports support UPOE+ / IEEE 802.3bt Type 4"),
            routing_throughput_mbps=n(10000, "Published firewall throughput; routing-performance field retains the original metric name in evidence"),
            uplink_interfaces=t("2 x dedicated 10GbE SFP+ WAN; 2 x convertible 10GbE LAN/WAN interfaces"),
            vpn_throughput_mbps=n(5000, "Maximum site-to-site VPN throughput"),
            vpn_tunnels=n(3000, "Maximum site-to-site VPN tunnels in lab testing"),
            wan_interfaces=t("2 x dedicated 10GbE SFP+ WAN; 2 x convertible 10GbE LAN/WAN interfaces"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Meraki MX67/MX67W/MX85 and Secure Router MX specifications."
    products = PRODUCTS
    document_version = "Cisco MX Family Data Sheet, updated 2026-09-01; accessed 2026-10-16"
    brand_name = "Cisco"
