from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "WAX605": {
        "url": "https://kb.netgear.com/000066106/WAX605-Firmware-Version-10-8-0-12",
        "page": "firmware feature list",
        "title": "NETGEAR WAX605 Firmware Version 10.8.0.12 Release Notes",
        "values": {
            "max_clients": n(128, "128 concurrent client connections; 64 clients per radio"),
            "fast_roaming": t("802.11r fast roaming in Insight mode"),
        },
    },
    "WAX610": {
        "url": "https://www.netgear.com/business/wifi/access-points/wax610/",
        "page": "current technical specifications",
        "title": "NETGEAR WAX610 Product Page",
        "values": {"max_clients": n(250, "Number of max users; 50 concurrent users recommended")},
    },
    "WAX620": {
        "url": "https://www.netgear.com/ca-en/business/wifi/access-points/wax620/",
        "page": "current product specifications",
        "title": "NETGEAR WAX620 Product Page",
        "values": {"max_clients": n(256, "Number of max users; 75 concurrent users recommended")},
    },
}


class Command(VerifiedImportCommand):
    help = "Import official NETGEAR WAX605/WAX610/WAX620 client limits and WAX605 fast roaming."
    products = PRODUCTS
    document_version = "Current official NETGEAR product pages and firmware notes; accessed 2026-10-20"
    brand_name = "NETGEAR"
