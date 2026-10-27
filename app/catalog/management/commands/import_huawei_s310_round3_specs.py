from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/9568f7a74e9d44c19f2d70d08ba21fd3/M3T1A590N1178058685920321688/Huawei%20ekitEngine%20S310%20Series%20Switches%20Datasheet.pdf"

PRODUCTS = {
    "S310-24T4X": {
        "url": SOURCE_URL,
        "page": "Service Features - IP routing",
        "title": "Huawei eKitEngine S310 Series Switches Datasheet",
        "values": {
            "routing_entry_capacity": t("Up to 512 IPv4 FIB entries and 512 IPv6 FIB entries"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Fill the remaining published Huawei S310-24T4X routing capacity."
    products = PRODUCTS
    document_version = "Official current global S310 datasheet; accessed 2026-10-20"
    brand_name = "Huawei"
