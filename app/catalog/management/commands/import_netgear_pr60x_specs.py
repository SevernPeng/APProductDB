from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    na,
    t,
)


URL = "https://www.downloads.netgear.com/files/GDC/PR60X/PR60X_DS.pdf"


PRODUCTS = {
    "PR60X": {
        "url": URL,
        "page": "pp. 3, 5-7, technical specifications; document NG_DS_ENT_PR60X-060526",
        "title": "NETGEAR PR60X 10G/Multi-Gigabit Dual WAN Pro Router Data Sheet",
        "values": {
            "concurrent_sessions": n(60000, "Concurrent connection limit: 60,000"),
            "controller_management": t(
                "NETGEAR Insight Remote Cloud Management; optional Insight Security Center/Exium dashboard"
            ),
            "dimensions_mm": t("440 x 100 x 43.2 mm (W x D x H)"),
            "firewall_features": t(
                "Firewall traffic rules and scheduling; port forwarding/triggering; SPI; "
                "port/service blocking; DoS prevention; stealth mode; TCP/UDP flood blocking; "
                "optional Exium IDS/IPS, DNS and web filtering"
            ),
            "lan_interfaces": t(
                "3 x 2.5G/1G RJ45 LAN; 1 x 10G/1G SFP+ LAN; "
                "1 x 10G/5G/2.5G/1G/100M RJ45 configurable as LAN or WAN"
            ),
            "operating_temperature_c": t("0 to 40 °C"),
            "routing_throughput_mbps": n(
                9400, "LAN-to-WAN throughput: 9.4 Gbps through the 10G configurable WAN port"
            ),
            "uplink_interfaces": t(
                "1 x 2.5G/1G RJ45 WAN; 1 x 10G/5G/2.5G/1G/100M RJ45 configurable LAN/WAN"
            ),
            "usb_interfaces": na("No USB interface is listed in the complete official hardware interface table"),
            "vpn_protocols": t(
                "IPSec site-to-site; IPSec client-to-site; OpenVPN client-to-site; WireGuard; "
                "IKEv1/IKEv2"
            ),
            "vpn_throughput_mbps": n(
                8920, "Maximum site-to-site VPN throughput: 8.92 Gbps on the 10G WAN port"
            ),
            "vpn_tunnels": n(30, "Up to 30 IPSec site-to-site VPN tunnels"),
            "wan_interfaces": t(
                "1 x 2.5G/1G RJ45 WAN; 1 x 10G/5G/2.5G/1G/100M RJ45 configurable LAN/WAN"
            ),
            "wan_load_balancing": b(True, "Dual WAN load balancing: Yes"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR PR60X gateway specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR datasheet NG_DS_ENT_PR60X-060526; accessed 2026-10-20"
    brand_name = "NETGEAR"
