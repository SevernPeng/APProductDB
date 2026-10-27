from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


SOURCE_URL = (
    "https://info.support.huawei.com/enterprise/en/doc/EDOC1100333403/"
    "cdd85713/basic-interface-configuration-commands"
)

MODELS = (
    "S5731-S24N4X2Q",
    "S5731-S24P4X",
    "S5731-S24T4X",
    "S5731-S24UN4X2Q",
    "S5731-S48P4X",
    "S5731-S48T4X",
)

PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "display interface output and S5731-S applicability notes",
        "title": "Huawei S-Series V200R023C00 Basic Interface Configuration Commands",
        "values": {
            "jumbo_frame_bytes": n(
                9216,
                "Official S5731-S command reference shows the maximum frame length as 9216 bytes",
            ),
        },
    }
    for model in MODELS
}


class Command(VerifiedImportCommand):
    help = "Import the official 9216-byte jumbo-frame limit for Huawei S5731-S switches."
    products = PRODUCTS
    document_version = "V200R023C00 official command reference; accessed 2026-10-22"
    brand_name = "Huawei"
