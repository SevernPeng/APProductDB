from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "SE3005": {
        "url": "https://support.linksys.com/kb/article/4998-en/",
        "page": "Specifications / Product Features / Power",
        "title": "Linksys SE3005 Support Page",
        "values": {
            "max_power_consumption_w": n(
                6,
                "Newest listed hardware version (v2) power input is 12 V at 0.5 A; adapter rating = 6 W",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the current Linksys SE3005 v2 power rating from official support specifications."
    products = PRODUCTS
    document_version = "Official Linksys SE3005 v1/v2 support specifications; newest v2 selected; accessed 2026-10-27"
    brand_name = "Linksys"
