from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = "https://techspecs.ui.com/unifi/switching/usw-enterprise-24-poe"


PRODUCTS = {
    "USW-Enterprise-24-PoE": {
        "url": URL,
        "page": "Performance - Packet Buffer Size",
        "title": "Ubiquiti UniFi Enterprise 24 PoE (Vintage) Tech Specs",
        "values": {
            "packet_buffer_mb": n(2, "Packet Buffer Size: 2 MB"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Correct the Ubiquiti USW-Enterprise-24-PoE packet-buffer value from current official Tech Specs."
    products = PRODUCTS
    document_version = "Current official Tech Specs page; accessed 2026-10-23"
    brand_name = "Ubiquiti"
