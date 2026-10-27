from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    t,
)


URL = "https://www.hpe.com/us/en/collaterals/collateral.a00062175enw.html"

PRODUCTS = {
    "R9M77A": {
        "url": URL,
        "page": "Power Options tables for Instant On AP22 and AP25",
        "title": "HPE Networking Instant On Wi-Fi 6 Access Points QuickSpecs",
        "values": {
            "accessory_compatibility": t(
                "HPE Networking Instant On AP22 and AP25",
                "R9M77A is listed as a selectable 30 W 802.3at PoE midspan injector for AP22 and AP25",
            ),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import officially listed R9M77A Instant On AP compatibility."
    products = PRODUCTS
    document_version = "Official HPE Instant On Wi-Fi 6 QuickSpecs; accessed 2026-10-22"
