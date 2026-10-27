from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


DOC = "https://documentation.grandstream.com/knowledge-base"


PRODUCTS = {
    "GWN7670": {
        "url": f"{DOC}/gwn7670-technical-specifications/",
        "page": "GWN7670 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7670 official technical specifications",
        "values": {
            "max_clients": n(256),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(2880),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "antenna_type": t("Five internal single-frequency antennas, including Bluetooth"),
            "operating_temperature_c": t("0 to 45 °C"),
            "max_power_consumption_w": n(15.5),
            "power_method": t("PoE (802.3af / 802.3at)"),
            "centralized_management": t("GDMS Networking cloud; GWN Manager on-premises; embedded controller"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7670E": {
        "url": f"{DOC}/gwn7670e-technical-specifications/",
        "page": "GWN7670E Technical Specifications, updated 2026",
        "title": "Grandstream GWN7670E official technical specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "max_clients": n(512),
            "ethernet_interfaces": t("1 x 2.5 Gigabit Ethernet PoE input port"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(2882),
            "rate_6g_mbps": na("Current official specification is dual-band and has no 6 GHz radio"),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("3x3:2 MU-MIMO"),
            "mimo_6g": na("Current official specification is dual-band and has no 6 GHz radio"),
            "total_spatial_streams": n(4, "Two spatial streams on each of the two concurrent radios"),
            "antenna_type": t("Five internal single-frequency antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.5 dBi; 5 GHz: 5.5 dBi"),
            "dimensions_mm": t("220 mm diameter x 48.5 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
            "max_power_consumption_w": n(16),
            "wireless_range": t("Up to 175 m; environment dependent"),
            "centralized_management": t("GDMS Networking cloud; GWN Manager on-premises; embedded controller"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7670WM": {
        "url": f"{DOC}/gwn7670wm-technical-specifications/",
        "page": "GWN7670WM Technical Specifications, updated 2026",
        "title": "Grandstream GWN7670WM official technical specifications",
        "values": {
            "max_clients": n(256),
            "ethernet_interfaces": t("1 x 2.5 Gigabit Ethernet RJ45 port"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(2882),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "dimensions_mm": t("150 x 106 x 34.1 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
            "power_method": t("PoE (802.3af / 802.3at)"),
            "centralized_management": t("GDMS Networking cloud; GWN Manager on-premises; embedded controller"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7670/7670E/7670WM specifications."
    products = PRODUCTS
    document_version = "Grandstream official technical documentation updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
