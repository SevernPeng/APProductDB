from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL_9105 = (
    "https://www.cisco.com/c/en/us/products/collateral/wireless/"
    "catalyst-9100ax-access-points/guide-c07-744444.html"
)
URL_9120 = (
    "https://www.cisco.com/c/en/us/products/collateral/wireless/"
    "catalyst-9100ax-access-points/guide-c07-742311.html"
)


PRODUCTS = {
    "C9105AXI": {
        "url": URL_9105,
        "page": "Catalyst 9105 Power over Ethernet (PoE) Draw table",
        "title": "Cisco Catalyst 9105AX Series Access Points Deployment Guide",
        "values": {
            "max_power_consumption_w": n(
                11,
                "C9105AXI consumption at the powered device; Cisco states full functionality at 11 W",
            ),
        },
    },
    "CW9105AXW": {
        "url": URL_9105,
        "page": "Key features and Catalyst 9105 Power over Ethernet (PoE) Draw table",
        "title": "Cisco Catalyst 9105AX Series Access Points Deployment Guide",
        "values": {
            "max_clients": n(200, "Supports up to 200 Wi-Fi devices"),
            "max_power_consumption_w": n(
                25.5,
                "Maximum consumption at the powered device with 802.3at input and 10.5 W PoE output enabled",
            ),
        },
    },
    "C9120AXI": {
        "url": URL_9120,
        "page": "Catalyst 9120 key features",
        "title": "Cisco Catalyst 9120 Access Point Deployment Guide",
        "values": {
            "max_clients": n(500, "Supports up to 500 Wi-Fi devices"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact Cisco Catalyst 9105/9120 client-scale and power specifications."
    products = PRODUCTS
    document_version = "Official Cisco deployment guides checked 2026-10-23"
    brand_name = "Cisco"
