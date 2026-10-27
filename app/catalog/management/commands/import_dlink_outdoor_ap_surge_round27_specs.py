from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


SOURCE_URL = "https://www.dlink.com/en/for-business/wireless-ap/enterprise-access-point/outdoor"


PRODUCTS = {
    "DAP-E3620OU": {
        "url": SOURCE_URL,
        "page": "Outdoor Access Point, Surge and Wind Protection",
        "title": "D-Link Outdoor Access Point Product Category",
        "values": {
            "lightning_protection_kv": t("6 kV", "6 kV surge protection"),
        },
    },
    "DAP-X3060OU": {
        "url": SOURCE_URL,
        "page": "Outdoor Access Point, Surge and Wind Protection",
        "title": "D-Link Outdoor Access Point Product Category",
        "values": {
            "lightning_protection_kv": t("6 kV", "6 kV surge protection"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import D-Link current outdoor AP surge protection rating."
    products = PRODUCTS
    document_version = "Current official D-Link outdoor AP category page; accessed 2026-10-27"
    brand_name = "D-Link"
