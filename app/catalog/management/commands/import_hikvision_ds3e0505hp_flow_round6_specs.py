from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


SOURCE_URL = (
    "https://assets.hikvision.com/prd/public/all/doc/m000011310/"
    "DS-3E0505HP-E_Datasheet_20240315.pdf"
)


PRODUCTS = {
    "DS-3E0505HP-E": {
        "url": SOURCE_URL,
        "page": "p. 1, standards list",
        "title": "Hikvision DS-3E0505HP-E Datasheet",
        "values": {
            "flow_control": t(
                "IEEE 802.3x flow control",
                "IEEE 802.3x standard",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified flow-control support for Hikvision DS-3E0505HP-E."
    products = PRODUCTS
    document_version = "Official exact-model datasheet dated 2024-03-15; accessed 2026-10-23"
    brand_name = "Hikvision"
