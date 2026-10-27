from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


BASE = "https://www.engeniustech.com/in/products/wireless/outdoor-access-points"


PRODUCTS = {
    "ECW160": {
        "url": f"{BASE}/ecw160/",
        "page": "Technical Specifications and data sheet v1.0",
        "title": "EnGenius ECW160 official product specifications",
        "values": {
            "max_clients": n(128, "Maximum concurrent users: 128 per radio"),
            "ethernet_interfaces": t("1 x Gigabit Ethernet PoE+ port"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "rate_2g_mbps": n(400, "Maximum published 2.4 GHz data rate"),
            "rate_5g_mbps": n(867, "Maximum published 5 GHz data rate"),
            "mimo_2g": t("2x2:2 SU-MIMO"),
            "mimo_5g": t("2x2:2 SU-MIMO and MU-MIMO"),
            "total_spatial_streams": n(4, "Two spatial streams on each of two concurrent radios"),
            "lightning_protection_kv": t("1 kV surge protection"),
        },
    },
    "ECW270": {
        "url": f"{BASE}/ecw270/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW270 official product specifications",
        "values": {
            "max_clients": n(512, "Maximum concurrent users: 512 per radio"),
            "ethernet_interfaces": t("1 x 2.5 Gigabit Ethernet PoE++ port; 1 x Gigabit Ethernet port"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "rate_2g_mbps": n(1148, "Technical table maximum; marketing rounds this to 1,200 Mbps"),
            "rate_5g_mbps": n(2400, "Maximum published 5 GHz data rate"),
            "mimo_2g": t("4x4:4 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("4x4:4 SU-MIMO and MU-MIMO"),
            "total_spatial_streams": n(8, "Four spatial streams on each of two concurrent radios"),
            "lightning_protection_kv": t("1 kV surge protection"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW160 and ECW270 outdoor AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
