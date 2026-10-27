from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "AirEngine 5762C-10": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/d8f53d342acf4c7a864ffaec67d0ee95/M3T1A590N1068233258347155609/Huawei%20AirEngine%205762C-10-V2%20Access%20Point%20Datasheet.pdf",
        "page": "Current V2 official product page and datasheet",
        "title": "Huawei AirEngine 5762C-10-V2 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(2400),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(128),
            "max_ssids": n(8, "Per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE-in"),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(9.4),
            "dimensions_mm": t("Ø180 x 35 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mounting_options": t("Wall or ceiling"),
            "centralized_management": t("Huawei WLAN AC in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS"
            ),
        },
    },
    "AirEngine 6760R-51": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/11050655dd4d404f9aebeeeb8de4b832/M3T1A590N1247214433860268162/Huawei%20AirEngine%206760R-51%20_%20AirEngine%206760R-51E%20Access%20Points%20Datasheet.pdf",
        "page": "Current official product page and 2025 datasheet",
        "title": "Huawei AirEngine 6760R-51 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1150),
            "rate_5g_mbps": n(4800),
            "mimo_2g": t("4x4:4 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "total_spatial_streams": n(8),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "512 per radio"),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5G/5GE PoE-in; 1 x GE; 1 x 1G/10G SFP+; BLE 5.2"),
            "power_method": t("IEEE 802.3af/at/bt PoE; full 4x4 operation with 802.3bt"),
            "max_power_consumption_w": n(35.3, "Full 4x4 + 4x4 operation with IEEE 802.3bt"),
            "dimensions_mm": t("85 x 270 x 220 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
            "ip_rating": t("IP68"),
            "lightning_protection_kv": t("6 kA surge protection for Ethernet ports"),
            "antenna_type": t("Built-in smart directional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 11 dBi"),
            "centralized_management": t("Huawei WLAN AC/Agile Controller in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WIDS/WIPS"
            ),
        },
    },
    "AirEngine 6760R-51E": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/11050655dd4d404f9aebeeeb8de4b832/M3T1A590N1247214433860268162/Huawei%20AirEngine%206760R-51%20_%20AirEngine%206760R-51E%20Access%20Points%20Datasheet.pdf",
        "page": "Current official product page and 2025 datasheet",
        "title": "Huawei AirEngine 6760R-51E official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1150),
            "rate_5g_mbps": n(4800),
            "mimo_2g": t("4x4:4 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "total_spatial_streams": n(8),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "512 per radio"),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5G/5GE PoE-in; 1 x GE; 1 x 1G/10G SFP+; BLE 5.2"),
            "power_method": t("IEEE 802.3af/at/bt PoE; full 4x4 operation with 802.3bt"),
            "max_power_consumption_w": n(35.3, "Full 4x4 + 4x4 operation with IEEE 802.3bt"),
            "dimensions_mm": t("85 x 270 x 220 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
            "ip_rating": t("IP67 when fitted with the specified external antennas"),
            "lightning_protection_kv": t("5 kA antenna-port and 6 kA Ethernet-port surge protection"),
            "antenna_type": t("External antennas"),
            "centralized_management": t("Huawei WLAN AC/Agile Controller in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WIDS/WIPS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5762C-10-V2 and 6760R-51/51E specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and latest available datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
