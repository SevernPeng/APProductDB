from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "S310-24P4X": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/switch/1239142461494834432",
        "page": "Product specifications — iStack",
        "title": "Huawei eKit S310-24P4X Product Specifications",
        "values": {"stacking_units": n(4, "iStack: Up to 4 switches of the same series in a stack")},
    },
    "S310-24T4X": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/switch/1884238246624035356",
        "page": "Product specifications — iStack",
        "title": "Huawei eKit S310-24T4X Product Specifications",
        "values": {"stacking_units": n(4, "iStack: Up to 4 switches of the same series in a stack")},
    },
    "S310-48T4X": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/switch/1239141268399895808",
        "page": "Product specifications — iStack",
        "title": "Huawei eKit S310-48T4X Product Specifications",
        "values": {"stacking_units": n(4, "iStack: Up to 4 switches of the same series in a stack")},
    },
}


class Command(VerifiedImportCommand):
    help = "Import official Huawei eKitEngine S310 iStack unit limits."
    products = PRODUCTS
    document_version = "Current Huawei eKit product specifications; accessed 2026-10-23"
    brand_name = "Huawei"
