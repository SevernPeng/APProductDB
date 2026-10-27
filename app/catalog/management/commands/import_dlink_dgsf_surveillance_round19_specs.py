from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "DGS-F1006P-E": {
        "url": "https://www.dlink.com/in/en/products/dgs-f1006p-e-4ge-poe-1ge-uplink-250m-poe-switch",
        "page": "Product highlights and current product specification page",
        "title": "D-Link DGS-F1006P-E Product Page",
        "values": {
            "lightning_protection_kv": t(
                "6 kV",
                "Current official product page: Light protection 6KV",
            ),
        },
    },
    "DGS-F1010P-E": {
        "url": "https://www.dlink.com/in/en/products/dgs-f1010p-e-8ge-poe-2ge-uplink-250m-poe-switch",
        "page": "Product highlights and technical specifications",
        "title": "D-Link DGS-F1010P-E Product Page",
        "values": {
            "lightning_protection_kv": t(
                "6 kV",
                "Current official product page and datasheet: Light/lighting protection 6KV",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact surge/lightning protection for D-Link DGS-F surveillance switches."
    products = PRODUCTS
    document_version = "Current official India product pages and datasheets; accessed 2026-10-23"
    brand_name = "D-Link"
