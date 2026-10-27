from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "RG-AP840-I": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/indoor-access-point-series/rg-ap840-i",
        "page": "Product overview and feature description",
        "title": "Ruijie RG-AP840-I official product page",
        "values": {
            "fast_roaming": t(
                "Seamless roaming with Ruijie wireless controller",
                "The exact-model overview explicitly lists seamless roaming and operation with a Ruijie wireless controller",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified roaming support for Ruijie RG-AP840-I."
    products = PRODUCTS
    document_version = "Current official Ruijie exact-model page; accessed 2026-10-22"
    brand_name = "Ruijie"
