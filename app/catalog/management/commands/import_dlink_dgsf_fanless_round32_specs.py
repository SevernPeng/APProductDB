from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
)


PRODUCTS = {
    "DGS-F1006P-E": {
        "url": "https://www.dlink.com.au/home-solutions/DGS-F1006P-E-6-port-gigabit-poe-switch-with-4-long-reach-250m-poe-ports",
        "page": "Specifications / design",
        "title": "D-Link Australia DGS-F1006P-E Product Page",
        "values": {
            "fanless": b(
                True,
                "Official specification: Design = Metal|Fanless; Fanless Design for Silent Operation = Yes",
            ),
        },
    },
    "DGS-F1010P-E": {
        "url": "https://www.dlink.com.au/home-solutions/DGS-F1010P-E-10-port-gigabit-poe-switch-with-8-long-reach-250m-poe-ports",
        "page": "Specifications / design",
        "title": "D-Link Australia DGS-F1010P-E Product Page",
        "values": {
            "fanless": b(
                True,
                "Official specification: Design = Metal|Fanless; Fanless Design for Silent Operation = Yes",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import officially stated fanless design for D-Link DGS-F surveillance switches."
    products = PRODUCTS
    document_version = "Current official D-Link Australia product pages; accessed 2026-10-27"
    brand_name = "D-Link"
