from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


DATASHEET = (
    "https://www2.dlink.com/en/-/media/business_products/dss/200g/"
    "dss200ga1datasheetv102ww.pdf"
)


PRODUCTS = {
    "DSS-200G-28MP": {
        "url": DATASHEET,
        "page": "Technical specifications, performance table",
        "title": "D-Link DSS-200G Series Datasheet v1.02WW",
        "values": {
            "packet_buffer_mb": n(
                0.512,
                "Packet buffer: 4.1 Mbits (normalized to 0.512 MB at database precision)",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the exact D-Link DSS-200G-28MP packet-buffer specification."
    products = PRODUCTS
    document_version = "Official DSS-200G Series datasheet v1.02WW; accessed 2026-10-23"
    brand_name = "D-Link"
