from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = "https://help.ui.com/hc/en-us/articles/18039891529879-Jumbo-Frames"

MODELS = (
    "ECS-Aggregation",
    "US-16-XG",
    "USW-16-PoE",
    "USW-24",
    "USW-24-POE (95W)",
    "USW-48",
    "USW-48-POE (195W)",
    "USW-48-PoE",
    "USW-Aggregation",
    "USW-Enterprise-24-PoE",
    "USW-Enterprise-8-PoE",
    "USW-EnterpriseXG-24",
    "USW-Flex",
    "USW-Flex-2.5G-8-PoE",
    "USW-Flex-Mini",
    "USW-Lite-16-PoE",
    "USW-Lite-8-PoE",
    "USW-Pro-24",
    "USW-Pro-24-PoE",
    "USW-Pro-48",
    "USW-Pro-48-PoE",
    "USW-Pro-8-PoE",
    "USW-Pro-Aggregation",
    "USW-Pro-Max-16-PoE",
    "USW-Pro-Max-16-PoE (180W)",
    "USW-Pro-Max-24",
    "USW-Pro-Max-24-PoE",
    "USW-Pro-XG-10-PoE",
    "USW-Pro-XG-24",
    "USW-Pro-XG-24-PoE",
    "USW-Pro-XG-24-PoE (720W)",
)

PRODUCTS = {
    model: {
        "url": URL,
        "page": "MTU Size and Exceptions",
        "title": "Ubiquiti Help Center: Jumbo Frames",
        "values": {
            "jumbo_frame_bytes": n(
                9216,
                "On UniFi Switches and Gateways, the typical MTU size is 9216 bytes when using Jumbo Frames; "
                "the only listed exceptions are USG and USG-Pro gateways at 9000 bytes.",
            ),
        },
    }
    for model in MODELS
}


class Command(VerifiedImportCommand):
    help = "Import the official 9216-byte UniFi switch Jumbo Frames MTU."
    products = PRODUCTS
    document_version = "Current Ubiquiti Help Center guidance; accessed 2026-10-23"
    brand_name = "Ubiquiti"
