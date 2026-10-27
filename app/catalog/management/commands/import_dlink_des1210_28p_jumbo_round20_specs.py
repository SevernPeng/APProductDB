from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = (
    "https://support.dlink.com/resource/products/DES-1210-28P/REVC/"
    "DES-1210-28P_REVC_MANUAL_4.00_EN.PDF"
)


PRODUCTS = {
    "DES-1210-28P": {
        "url": URL,
        "page": "p. 37, L2 Functions > Jumbo Frame",
        "title": "D-Link DES-1210 Series Switch Web UI Reference Guide",
        "values": {
            "jumbo_frame_bytes": n(
                9216,
                "D-Link Gigabit Web Smart Switches support tagged jumbo frames up to 9216 bytes",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the exact DES-1210-28P Revision C jumbo-frame limit."
    products = PRODUCTS
    document_version = "Revision C Web UI Reference Guide 4.00; accessed 2026-10-23"
    brand_name = "D-Link"
