from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
)


SOURCE_URL = (
    "https://www2.dlink.com/lt/lt/-/media/resource-centre/brochures-and-product-guides/"
    "2025-q2-d-link-product-guide-eu.pdf"
)


WDS_MESH = b(
    True,
    "Official comparison lists multiple modes including WDS with AP and WDS/bridge; "
    "recorded under the database's existing broad mesh/WDS capability convention",
)


PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "Wireless AP comparison, Multiple modes (AP, WDS with AP, WDS/bridge, client)",
        "title": "D-Link 2025 Q2 Product Guide EU",
        "values": {"mesh_support": WDS_MESH},
    }
    for model in (
        "DAP-2622",
        "DAP-2680",
        "DAP-3666",
        "DAP-X2810",
        "DAP-X2850",
        "DAP-X3060",
    )
}


class Command(VerifiedImportCommand):
    help = "Import D-Link AP WDS capability using the database's mesh/WDS convention."
    products = PRODUCTS
    document_version = "D-Link 2025 Q2 EU product guide; accessed 2026-10-27"
    brand_name = "D-Link"
