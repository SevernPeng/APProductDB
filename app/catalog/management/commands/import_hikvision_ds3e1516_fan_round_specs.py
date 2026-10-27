from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    t,
)


SOURCE_URL = (
    "https://assets.hikvision.com/prd/public/all/doc/m000034944/"
    "DS-3E1516-EI_Datasheet_20240425.pdf"
)


PRODUCTS = {
    "DS-3E1516-EI": {
        "url": SOURCE_URL,
        "page": "p. 1, product highlights",
        "title": "Hikvision DS-3E1516-EI Datasheet",
        "values": {
            "fan_design": t(
                "Fan-free design",
                "Reliable fan-free design",
            ),
            "fanless": b(
                True,
                "Reliable fan-free design",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified cooling design for Hikvision DS-3E1516-EI."
    products = PRODUCTS
    document_version = "Official exact-model datasheet dated 2024-04-25; accessed 2026-10-23"
    brand_name = "Hikvision"
