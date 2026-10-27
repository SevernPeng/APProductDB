from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


SOURCE_URL = (
    "https://support.dlink.com/resource/PRODUCTS/DBS-2000-SERIES/REVA/"
    "DBS-2000-SERIES_REVA_NUCLIAS_CLOUD_MANUAL_v1.00_WW.pdf"
)


PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "p. 62, section 8.1.6.6 Configuring Jumbo Frame",
        "title": "D-Link DBS-2000 Series Nuclias Cloud Manual v1.00",
        "values": {
            "jumbo_frame_bytes": n(
                9000,
                "Jumbo Frame mode supports packets of up to 9,000 bytes",
            ),
        },
    }
    for model in ("DBS-2000-10MP", "DBS-2000-28P")
}


class Command(VerifiedImportCommand):
    help = "Import verified D-Link DBS-2000 jumbo-frame capacity."
    products = PRODUCTS
    document_version = "Official Nuclias Cloud Manual v1.00; accessed 2026-10-23"
    brand_name = "D-Link"
