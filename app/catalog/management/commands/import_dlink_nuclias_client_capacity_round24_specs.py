from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


SOURCE_URL = (
    "https://www.dlink.com/en/-/media/resource-centre/brochures-and-product-guides/"
    "nuclias-cloud-solution-guide.pdf"
)


PRODUCTS = {
    "DBA-2520P": {
        "url": SOURCE_URL,
        "page": "Access Point Comparison, Recommended Client Capacity",
        "title": "D-Link Nuclias Cloud Solution Guide",
        "values": {
            "max_clients": n(100, "Recommended client capacity: 100"),
        },
    },
    "DBA-X1230P": {
        "url": SOURCE_URL,
        "page": "Access Point Comparison, Recommended Client Capacity",
        "title": "D-Link Nuclias Cloud Solution Guide",
        "values": {
            "max_clients": n(150, "Recommended client capacity: 150"),
        },
    },
    "DBA-X2830P": {
        "url": SOURCE_URL,
        "page": "Access Point Comparison, Recommended Client Capacity",
        "title": "D-Link Nuclias Cloud Solution Guide",
        "values": {
            "max_clients": n(250, "Recommended client capacity: 250"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import D-Link Nuclias Cloud recommended AP client capacities."
    products = PRODUCTS
    document_version = "Current official D-Link Nuclias Cloud solution guide; accessed 2026-10-27"
    brand_name = "D-Link"
