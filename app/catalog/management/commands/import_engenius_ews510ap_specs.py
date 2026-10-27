from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "EWS510AP": {
        "url": "https://www.engeniustech.com/apac/products/wireless/indoor-access-points/ews510ap/",
        "page": "Technical Specifications (EOL product page)",
        "title": "EnGenius EWS510AP official product specifications",
        "values": {
            "mimo_5g": t("2x2:2"),
            "operating_temperature_c": t("0 to 50 °C"),
            "poe_output": t("1 x 10/100 Mbps access port with 802.3af PoE output when the uplink receives 802.3at"),
            "max_power_consumption_w": n(10.8, "Power consumption: up to 10.8 W"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius EWS510AP specifications."
    products = PRODUCTS
    document_version = "EnGenius official EOL product page; accessed 2026-10-16"
    brand_name = "EnGenius"
