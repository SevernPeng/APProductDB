from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "USW-Lite-8-PoE": {
        "url": "https://store.ui.com/us/en/category/all-switching/products/usw-lite-8-poe",
        "page": "Product overview",
        "title": "Ubiquiti Store: Lite 8 PoE",
        "values": {
            "fan_design": t("Silent fanless cooling", "Supports silent fanless cooling"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the official cooling design for the Ubiquiti Lite 8 PoE."
    products = PRODUCTS
    document_version = "Current Ubiquiti Store product page; accessed 2026-10-23"
    brand_name = "Ubiquiti"
