from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


SUPPORT = "https://support.linksys.com/kb/article/4998-en/"


PRODUCTS = {
    "SE3005": {
        "url": SUPPORT,
        "page": "Product Features, current support page (v1 and v2)",
        "title": "Linksys SE3005 Support",
        "values": {
            "flow_control": t(
                "IEEE 802.3x flow control",
                "Standards: IEEE 802.3, 802.3u, 802.3x, 802.3ab and 802.3az",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the verified Linksys SE3005 IEEE 802.3x flow-control specification."
    products = PRODUCTS
    document_version = "Current Linksys support page; accessed 2026-10-22"
    brand_name = "Linksys"
