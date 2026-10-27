from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "AirEngine 5562-17W": {
        "url": "https://carrier.huawei.com/~/media/cnbgv2/download/products/networks/wlan/indoor-access-points-airengine-5562-17w-pdf-en.pdf",
        "page": "Official product datasheet and current Huawei support hardware description",
        "title": "Huawei AirEngine 5562-17W official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(2400),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x GE uplink PoE-in; 4 x GE downlink; 1 x USB; BLE 5.1"),
            "poe_output": t("Not supported"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(15, "Excluding USB"),
            "dimensions_mm": t("160 x 86 x 38 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 2.5 dBi; 5 GHz: 3 dBi"),
            "mounting_options": t("Wall, ceiling, or junction box"),
            "centralized_management": t("Huawei WLAN AC in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; DTLS"
            ),
        },
    },
    "AirEngine 6576-57T": {
        "url": "https://carrier.huawei.com/~/media/cnbgv2/download/products/networks/wlan/huawei-airengine-6576-57t-access-point-datasheet-pdf-en.pdf",
        "page": "Current official product page and datasheet",
        "title": "Huawei AirEngine 6576-57T official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(689),
            "rate_5g_mbps": n(1440),
            "rate_6g_mbps": n(11530),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "mimo_6g": t("4x4:4 MIMO"),
            "total_spatial_streams": n(8),
            "max_channel_width_mhz": n(320),
            "max_clients": n(1800, "600 per radio"),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5G/5GE PoE-in; 1 x GE; 1 x USB; BLE 5.2"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(21.1, "Excluding USB"),
            "dimensions_mm": t("Ø220 x 45 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 5 dBi"),
            "mounting_options": t("Wall or ceiling"),
            "centralized_management": t("Huawei WLAN AC in Fit mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; PMF; WIDS/WIPS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5562-17W and 6576-57T specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages, datasheets, and support documentation; accessed 2026-10-19"
    brand_name = "Huawei"
