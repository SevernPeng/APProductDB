from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "RG-NBR6215-E": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/nbr-series/nbr6215-e",
        "page": "Official product page and key specifications",
        "title": "Ruijie Reyee RG-NBR6215-E official specifications",
        "values": {
            "routing_throughput_mbps": n(2500, "Up to 2.5 Gbps throughput"),
            "uplink_interfaces": t(
                "1 x fixed Gigabit WAN; 6 x Gigabit LAN/WAN; "
                "1 x 1G SFP LAN/WAN; 1 x 10G SFP+ LAN/WAN"
            ),
            "vpn_tunnels": n(1000, "Up to 1000 IPsec tunnels"),
            "firewall_features": t(
                "All-in-one security router with L7 DPI, network behavior audit, "
                "application rules and intelligent flow control in VPN tunnels"
            ),
            "controller_management": t("Ruijie Cloud platform and Ruijie Cloud app"),
            "max_power_consumption_w": n(25, "Less than 25 W"),
            "dimensions_mm": t("440 x 43.6 x 200 mm"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie Reyee RG-NBR6215-E specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie Reyee product page; accessed 2026-10-16"
    brand_name = "Ruijie"
