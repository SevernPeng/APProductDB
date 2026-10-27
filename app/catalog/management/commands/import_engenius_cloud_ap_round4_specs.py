from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


BASE = "https://www.engeniustech.com/in/products/wireless/indoor-access-points"


def values(clients, ethernet):
    return {
        "max_clients": n(clients, "Maximum concurrent users"),
        "ethernet_interfaces": t(ethernet),
        "operating_temperature_c": t("0 to 40 °C"),
        "mimo_2g": t("2x2:2 SU-MIMO and MU-MIMO"),
        "mimo_5g": t("2x2:2 SU-MIMO and MU-MIMO"),
        "total_spatial_streams": n(4, "Two spatial streams on each of two concurrent radios"),
    }


PRODUCTS = {
    "ECW510": {
        "url": f"{BASE}/ecw510/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW510 official product specifications",
        "values": values(512, "1 x 2.5 Gigabit Ethernet PoE+ port; 1 x DC jack"),
    },
    "ECW510P": {
        "url": f"{BASE}/ecw510p/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW510P official product specifications",
        "values": values(256, "1 x 2.5 Gigabit Ethernet PoE+ port; 1 x DC jack"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW510 and ECW510P AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages; accessed 2026-10-16"
    brand_name = "EnGenius"
