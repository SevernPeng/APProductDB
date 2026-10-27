from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
)


GUIDE = "https://www.dlink.com/fr/fr/-/media/resource-centre/brochures-and-product-guides/2026-q1-dlink-product-guide.pdf"


PRODUCTS = {
    "DAP-X3060W": {
        "url": GUIDE,
        "page": "Access point comparison table, DAP-X3060W column",
        "title": "D-Link 2026 Q1 Product Guide",
        "values": {
            "max_ssids": n(16, "Maximum number of SSIDs: 16"),
        },
    },
    "DAP-E3620": {
        "url": GUIDE,
        "page": "Access point comparison table, DAP-E3620 column",
        "title": "D-Link 2026 Q1 Product Guide",
        "values": {
            "mesh_support": b(
                True,
                "Official comparison lists multiple modes: AP, WDS with AP, WDS/bridge and client; recorded under the database's WDS/mesh convention",
            ),
        },
    },
    "DAP-E9560": {
        "url": GUIDE,
        "page": "Access point comparison table, DAP-E9560 column",
        "title": "D-Link 2026 Q1 Product Guide",
        "values": {
            "mesh_support": b(
                True,
                "Official comparison lists multiple modes: AP, WDS with AP, WDS/bridge and client; recorded under the database's WDS/mesh convention",
            ),
        },
    },
    "DES-F1017P-E": {
        "url": "https://www.dlink.com.vn/Downloads/DES-F1017P/datasheet/DES-F1017P-E%20DS.pdf",
        "page": "Physical specifications",
        "title": "D-Link DES-F1017P-E Datasheet",
        "values": {
            "max_power_consumption_w": n(
                150,
                "Physical/Power: external power adapter 150 W; official table also states a 150 W total power budget",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Complete current D-Link AP comparison fields and DES-F1017P-E power rating."
    products = PRODUCTS
    document_version = "D-Link 2026 Q1 product guide and official DES-F1017P-E datasheet; accessed 2026-10-27"
    brand_name = "D-Link"
