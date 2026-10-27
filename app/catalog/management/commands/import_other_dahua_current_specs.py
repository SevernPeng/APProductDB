from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "Dahua PFS3211-8GT-120": {
        "url": "https://www.dahuasecurity.com/br/products/Dedicated-Products/Project-Exclusive/Transmission/PFS3211-8GT-120",
        "page": "Technical Specification table",
        "title": "Dahua PFS3211-8GT-120 Official Product Specifications",
        "values": {
            "mac_address_table": t("4K entries", "MAC Table Size: 4K"),
        },
    },
    "Dahua PFS4207-4GT-DP": {
        "url": "https://www.dahuasecurity.com/in/products/Transmission/PoE-Switches/Industrial-PoE-Switch/PFS4207-4GT-DP",
        "page": "Hardware specifications, Power Consumption",
        "title": "Dahua PFS4207-4GT-DP Official Product Specifications",
        "values": {
            "max_power_consumption_w": n(120, "Power Consumption — Full load: 120 W; idling: <= 9 W"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current verified specifications for legacy Dahua records under Other."
    products = PRODUCTS
    document_version = "Current Dahua official product specifications; accessed 2026-10-21"
    brand_name = "Other"
