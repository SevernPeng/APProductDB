from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
)


SOURCE_URL = (
    "https://www.dlink.com/en/-/media/product-pages/dss/dss-100e-18p/assets/"
    "dss100eseriesa1datasheetv100ww.pdf"
)


PRODUCTS = {
    "DSS-100E-18P": {
        "url": SOURCE_URL,
        "page": "pp. 2-3, DSS-100E-18P column in the technical-specifications table",
        "title": "D-Link DSS-100E Series Unmanaged Surveillance Switch Datasheet",
        "values": {
            "switching_capacity_gbps": n(
                7.2,
                "DSS-100E-18P switching capacity: 7.2 Gbps",
            ),
            "packet_forwarding_rate_mpps": n(
                5.36,
                "DSS-100E-18P forwarding rate: 5.36 Mpps",
            ),
            "poe_budget_w": n(
                230,
                "DSS-100E-18P PoE power budget: 230 W",
            ),
            "max_power_consumption_w": n(
                265,
                "DSS-100E-18P maximum power consumption with PoE on (AC): 265.0 W",
            ),
            "fanless": b(
                False,
                "DSS-100E-18P acoustics: 38.4 dB(A); the switch is not fanless",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Correct column-shifted D-Link DSS-100E-18P B1 specifications."
    products = PRODUCTS
    document_version = "Official DSS-100E Series B1 datasheet v1.00 WW; accessed 2026-10-23"
    brand_name = "D-Link"
