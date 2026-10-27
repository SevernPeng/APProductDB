from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SECURITY = (
    "WPA2-Personal/Enterprise; WPA3-Personal/Enterprise; WPA/WPA2 and WPA2/WPA3 "
    "mixed modes; PPSK/DPSK; WAPI; 802.11w PMF; WIDS/WIPS"
)


HIGH_END_SOURCE = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "40764568d113493d899de3de77301291/M3T1A590N1186032560931410210/"
    "Huawei%20AirEngine%208776-X7T-T%20_%20AirEngine%208776-X7ET-T%20Access%20Points%20Datasheet.pdf"
)


def high_end_common(antenna_type):
    return {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "mimo_2g": t("4x4:4 MU-MIMO"),
        "mimo_5g": t("4x4:4 MU-MIMO"),
        "mimo_6g": t("4x4:4 MU-MIMO"),
        "total_spatial_streams": n(12),
        "max_channel_width_mhz": n(320),
        "max_clients": n(1800, "600 per radio"),
        "max_ssids": n(16, "Per radio"),
        "ethernet_interfaces": t(
            "2 x 100M/1G/2.5G/5G/10GE PoE-in; USB; Bluetooth 6.0; built-in multi-protocol IoT interfaces"
        ),
        "power_method": t("43.2-57.6 V DC or IEEE 802.3at/bt PoE"),
        "max_power_consumption_w": n(35.2, "Excluding USB"),
        "dimensions_mm": t("54 x 265 x 265 mm"),
        "operating_temperature_c": t("-10 to 50 °C"),
        "antenna_type": t(antenna_type),
        "centralized_management": t(
            "Huawei WLAN AC in Fit mode; local Fat mode; Huawei cloud management platform"
        ),
        "mesh_support": b(True),
        "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
        "wireless_security": t(SECURITY),
    }


PRODUCTS = {
    "6776-58TI": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/9ea1071a01ff4e43811cfb19f2710864/M3T1A590N1198217455589752867/Huawei%20AirEngine%206776-58TI%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, V600R25C00, pp. 2-10",
        "title": "Huawei AirEngine 6776-58TI official product datasheet",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(689),
            "rate_5g_mbps": n(5760),
            "rate_6g_mbps": n(1440),
            "mimo_2g": t("2x2:2 or 4x4:4 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "mimo_6g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(8),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1800),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t(
                "1 x 100M/1G/2.5G/5GE PoE-in; 1 x 10/100/1000BASE-T PoE-in; "
                "dual PoE input hot backup; USB; BLE 5.4; two PCIe IoT slots"
            ),
            "power_method": t("43.2-57.6 V DC or IEEE 802.3at/bt PoE with dual-input hot backup"),
            "max_power_consumption_w": n(23.9, "Excluding USB and IoT cards"),
            "dimensions_mm": t("61 x 220 x 220 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t(
                "2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 5 dBi (single-antenna peak gain)"
            ),
            "centralized_management": t(
                "Huawei WLAN AC in Fit mode or Huawei cloud management platform"
            ),
            "mesh_support": b(True),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming"),
            "wireless_security": t(SECURITY),
        },
    },
    "AirEngine 8776-X7T-T": {
        "url": HIGH_END_SOURCE,
        "page": "Current official datasheet, pp. 2-11",
        "title": "Huawei AirEngine 8776-X7T-T official product datasheet",
        "values": {
            **high_end_common("Built-in dynamic-zoom smart antennas"),
            "antenna_gain_dbi": t(
                "2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 5 dBi (single-antenna peak gain)"
            ),
        },
    },
    "AirEngine 8776-X7ET-T": {
        "url": HIGH_END_SOURCE,
        "page": "Current official datasheet, pp. 2-11",
        "title": "Huawei AirEngine 8776-X7ET-T official product datasheet",
        "values": high_end_common("External antennas; gain depends on the selected antenna"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei high-performance Wi-Fi 7 AP specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
