from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "S5731-S24UN4X2Q": {
        "url": "https://e.huawei.com/mx/products/switches/campus-switches/s5731-s-multi-ge",
        "page": "Specifications table; global-region values",
        "title": "Huawei CloudEngine S5731-S Series Multi-GE Switches",
        "values": {
            "switching_capacity_gbps": n(
                360,
                "Device switching capacity before the slash; global-region specification is 360/672 Gbps",
            ),
            "packet_forwarding_rate_mpps": n(125),
            "operating_temperature_c": t(
                "-5 to 45 °C at 0-1800 m; maximum temperature derates above 1800 m"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Correct current global Huawei S5731-S24UN4X2Q specifications from official sources."
    products = PRODUCTS
    document_version = "Current official global product page and Info-Finder; accessed 2026-10-20"
    brand_name = "Huawei"
