from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


SOURCE_URL = "https://download.zyxel.com/GS1200-5/user_guide/GS1200-5_V2.00_Ed4.pdf"

MODELS = (
    "GS1200-5",
    "GS1200-8",
    "GS1200-5HP",
)

PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "Chapter 6 VLAN tutorial and Chapter 8 Port settings",
        "title": "Zyxel GS1200 Series User's Guide V2.00 Edition 4",
        "values": {
            "vlan_count": n(
                32,
                "Maximum number of IEEE 802.1Q VLAN: 32",
            ),
            "stp_features": t(
                "Loop detection / prevention",
                "Port settings provide Loop Detection / Prevention; the guide does not identify this as STP or RSTP",
            ),
        },
    }
    for model in MODELS
}


class Command(VerifiedImportCommand):
    help = "Import verified VLAN capacity and loop-protection features for Zyxel GS1200 switches."
    products = PRODUCTS
    document_version = "V2.00 Edition 4, 2024-12-03; accessed 2026-10-22"
    brand_name = "Zyxel"
