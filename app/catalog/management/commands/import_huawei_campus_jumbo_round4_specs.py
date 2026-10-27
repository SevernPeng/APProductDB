from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


SOURCE_URL = (
    "https://info.support.huawei.com/enterprise/en/doc/EDOC1100333403/"
    "cdd85713/basic-interface-configuration-commands"
)

MODELS = (
    "S5735-L24PN4XE-A-V2",
    "S5735-L48LPN4XE-A-V2",
    "S5735-S24PN4XE-V2",
    "S5735-S24T4XE-C-V2",
    "S5735-S48PN4XE-V2",
    "S6730-H28Y4C",
    "S6730-H48X6C-V2",
)

PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "display interface output and family applicability notes",
        "title": "Huawei S-Series V200R023C00 Basic Interface Configuration Commands",
        "values": {
            "jumbo_frame_bytes": n(
                9216,
                "Official command reference for the S5735-L/S5735-S/S6730-H families shows a 9216-byte maximum frame length",
            ),
        },
    }
    for model in MODELS
}


class Command(VerifiedImportCommand):
    help = "Import verified 9216-byte jumbo-frame limits for Huawei campus switches."
    products = PRODUCTS
    document_version = "V200R023C00 official command reference; accessed 2026-10-22"
    brand_name = "Huawei"
