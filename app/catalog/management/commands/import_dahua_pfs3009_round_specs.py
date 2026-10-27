from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
)


CATALOG = "https://materialfile.dahuasecurity.com/uploads/soft/20241127/Catalog_Dahua-Network-Transmission-Products-and-Solutions_V1.0_EN_202409%281%29.pdf"


PRODUCTS = {
    "PFS3009-8ET-65": {
        "url": CATALOG,
        "page": "p. 23, Desktop PoE Switch comparison table",
        "title": "Dahua Network Transmission Products and Solutions Catalog",
        "values": {
            "poe_auto_recovery": b(False, "PoE Watchdog: --"),
            "extend_mode": b(False, "Long Distance PoE Transmission: --"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified unsupported PoE Watchdog and long-distance mode values for Dahua PFS3009-8ET-65."
    products = PRODUCTS
    document_version = "V1.0, September 2024; accessed 2026-10-22"
    brand_name = "Dahua"
