from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = "https://instant-on.hpe.com/techdocs/en/content/get-started/deploy-types.htm"


PRODUCTS = {
    "AP22D": {
        "url": URL,
        "title": "HPE Networking Instant On Help Center - Instant On Deployment Concepts",
        "page": "Access Point Only Deployment",
        "values": {
            "max_ssids": n(
                8,
                "Instant On AP-only deployments allow a maximum of 8 wireless networks (SSIDs) per site",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the official Instant On AP22D wireless-network/SSID limit."
    products = PRODUCTS
    document_version = "Current official Instant On Help Center; accessed 2026-10-21"
    brand_name = "Instant On"
