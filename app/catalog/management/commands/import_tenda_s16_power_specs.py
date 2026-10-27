from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "S16": {
        "url": "https://www.tendacn.com/ae/product/specification/S16",
        "page": "Hardware / Power",
        "title": "Tenda S16 Product Specification",
        "values": {
            "max_power_consumption_w": n(
                5.4,
                "Official external adapter output rating: 9 V at 0.6 A = 5.4 W",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the official Tenda S16 power-adapter rating."
    products = PRODUCTS
    document_version = "Current official Tenda S16 product specification; accessed 2026-10-27"
    brand_name = "Tenda"
