from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
)


PRODUCTS = {
    "DAP-E3620": {
        "url": "https://d-link.ru/en/products/2/2806.html",
        "page": "Wireless Module Parameters / transmitter output power",
        "title": "D-Link DAP-E3620 Product Page",
        "values": {
            "max_channel_width_mhz": n(
                160,
                "Official radio table explicitly lists 5 GHz EHT20/EHT40/EHT80/EHT160",
            ),
        },
    },
    "DAP-E3620OU": {
        "url": "https://www.dlink.ru/mn/products/2/2808.html",
        "page": "Multiple Operation Modes and Wireless Module Parameters",
        "title": "D-Link DAP-E3620OU Product Page",
        "values": {
            "max_channel_width_mhz": n(
                160,
                "Official radio table explicitly lists 5 GHz EHT20/EHT40/EHT80/EHT160",
            ),
            "mesh_support": b(
                True,
                "Official page explicitly supports Access Point, WDS and WDS with AP; recorded under the database's WDS/mesh convention",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact D-Link DAP-E3620 series channel width and WDS/mesh support."
    products = PRODUCTS
    document_version = "Current official D-Link regional product pages; accessed 2026-10-27"
    brand_name = "D-Link"
