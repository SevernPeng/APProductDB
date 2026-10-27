from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


DOC = "https://documentation.grandstream.com/knowledge-base"
MANAGEMENT = "GDMS Networking cloud; GWN Manager on-premises; embedded controller"


PRODUCTS = {
    "GWN7672": {
        "url": "https://www.grandstream.com/hubfs/Product_Documentation/GWN7672/Datasheet_GWN7672_English.pdf",
        "page": "Official datasheet 10.2025 v1 and current technical documentation",
        "title": "Grandstream GWN7672 official datasheet",
        "values": {
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(4320),
            "rate_6g_mbps": n(5765),
            "operating_temperature_c": t("0 to 45 °C"),
            "wireless_range": t("Up to 175 m; environment dependent"),
            "centralized_management": t(MANAGEMENT),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7672L": {
        "url": f"{DOC}/gwn7672l-technical-specifications/",
        "page": "GWN7672L Technical Specifications, updated 2026",
        "title": "Grandstream GWN7672L official technical specifications",
        "values": {
            "max_clients": n(384),
            "ethernet_interfaces": t("1 x 5 Gigabit Ethernet RJ45 PoE input port"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(4320),
            "rate_6g_mbps": n(5765),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "mimo_6g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(6),
            "antenna_type": t("Six internal single-frequency antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.5 dBi; 5 GHz: 5.5 dBi; 6 GHz: 5.5 dBi"),
            "dimensions_mm": t("220 mm diameter x 48.5 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
            "centralized_management": t(MANAGEMENT),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7672WM": {
        "url": f"{DOC}/gwn7672wm-technical-specifications/",
        "page": "GWN7672WM Technical Specifications, updated 2026",
        "title": "Grandstream GWN7672WM official technical specifications",
        "values": {
            "max_clients": n(384),
            "ethernet_interfaces": t("1 x 5 Gigabit Ethernet RJ45 PoE input port"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(4320),
            "rate_6g_mbps": n(5765),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "mimo_6g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(320),
            "max_ssids": n(48),
            "antenna_type": t("Seven internal single-frequency antennas, including Bluetooth"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 6 dBi; Bluetooth: 4 dBi"),
            "dimensions_mm": t("168.95 x 118.95 x 39.1 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
            "power_method": t("PoE+ (802.3at)"),
            "max_power_consumption_w": n(25.5),
            "centralized_management": t(MANAGEMENT),
            "wireless_security": t("WPA2/WPA3, Enhanced Open, PMF, secure boot, WIDS and client isolation"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7673": {
        "url": f"{DOC}/gwn7673-technical-specifications/",
        "page": "GWN7673 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7673 official technical specifications",
        "values": {
            "max_clients": n(512),
            "ethernet_interfaces": t("1 x 2.5 Gigabit Ethernet RJ45 PoE input port"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(4323),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("3x3:3 MU-MIMO"),
            "total_spatial_streams": n(5),
            "antenna_type": t("Five internal single-frequency antennas"),
            "dimensions_mm": t("220 mm diameter x 48.5 mm"),
            "power_method": t("PoE (802.3af / 802.3at)"),
            "centralized_management": t("Local Web UI; GDMS Networking; GWN Manager; GWN App"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7672/L/WM and GWN7673 specifications."
    products = PRODUCTS
    document_version = "Grandstream official datasheet and technical documentation updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
