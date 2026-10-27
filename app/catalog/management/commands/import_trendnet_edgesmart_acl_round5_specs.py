from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


CATALOG_URL = (
    "https://download.trendnet.com/Marketing/catalog_2019/"
    "2019_product_catalog071719.pdf"
)

PRODUCTS = {
    "TEG-S50ES": {
        "url": CATALOG_URL,
        "page": "Managed Switches comparison table, ACL row",
        "title": "TRENDnet 2019 Product Catalog",
        "values": {
            "acl_security": t(
                "Not supported",
                "ACL: '-' for TEG-S50ES in the official managed-switch comparison table",
            ),
        },
    },
    "TEG-S80ES": {
        "url": CATALOG_URL,
        "page": "Managed Switches comparison table, ACL row",
        "title": "TRENDnet 2019 Product Catalog",
        "values": {
            "acl_security": t(
                "Not supported",
                "ACL: '-' for TEG-S80ES in the official managed-switch comparison table",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import official TRENDnet EdgeSmart ACL support values."
    products = PRODUCTS
    document_version = "Official TRENDnet product catalog, July 2019; accessed 2026-10-27"
    brand_name = "TRENDnet"
