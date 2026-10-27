from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "ECW536S": {
        "url": "https://www.engeniustech.com/apac/products/wireless/indoor-access-points/ecw536s/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW536S official product specifications",
        "values": {
            "max_clients": n(512, "Maximum concurrent users"),
            "ethernet_interfaces": t("1 x 10 Gigabit Ethernet PoE++ port; 1 x 10 Gigabit Ethernet port; 1 x DC jack"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "ECW560": {
        "url": "https://www.engeniustech.com/eu/products/wireless/outdoor-access-points/ecw560/",
        "page": "Technical Specifications and data sheet v1.2 dated 2026-07-15",
        "title": "EnGenius ECW560 official product specifications",
        "values": {
            "max_clients": n(512, "Maximum concurrent users"),
            "ethernet_interfaces": t("1 x 2.5 Gigabit Ethernet PoE+ port; 1 x 2.5 Gigabit Ethernet port"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "lightning_protection_kv": t("1 kV surge protection"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW536S and ECW560 AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
