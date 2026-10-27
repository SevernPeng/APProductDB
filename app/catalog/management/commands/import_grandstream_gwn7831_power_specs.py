from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "GWN7831": {
        "url": "https://documentation.grandstream.com/knowledge-base/gwn78xx-power-consumption-information/",
        "page": "GWN78xx power-consumption table, GWN7831 row, updated 2026",
        "title": "Grandstream GWN78xx power consumption information",
        "values": {
            "max_power_consumption_w": n(38.96, "100% traffic power consumption"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import Grandstream GWN7831 power consumption from the official bulletin."
    products = PRODUCTS
    document_version = "Grandstream GWN78xx power-consumption bulletin updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
