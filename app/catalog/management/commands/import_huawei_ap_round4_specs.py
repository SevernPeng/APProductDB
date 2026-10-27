from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


OUTDOOR_SOURCE = (
    "https://e.huawei.com/en/products/wlan/outdoor-access-points/"
    "airengine-5761r-11-airengine-5761r-11e"
)


def outdoor_common(max_power, antenna_type, max_rate_5g=1200):
    return {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(575),
        "rate_5g_mbps": n(max_rate_5g),
        "mimo_2g": t("2x2:2 MU-MIMO"),
        "mimo_5g": t("2x2:2 MU-MIMO"),
        "total_spatial_streams": n(4),
        "max_channel_width_mhz": n(80),
        "max_clients": n(1024),
        "max_ssids": n(16, "Per radio"),
        "ethernet_interfaces": t(
            "1 x 10/100/1000BASE-T PoE-in; 1 x GE SFP supporting GE optical or GPON module"
        ),
        "power_method": t("IEEE 802.3af/at PoE"),
        "max_power_consumption_w": n(max_power),
        "dimensions_mm": t("70 x 200 x 200 mm"),
        "operating_temperature_c": t("-40 to 65 °C"),
        "antenna_type": t(antenna_type),
        "ip_rating": t("IP68"),
        "lightning_protection_kv": t(
            "5 kA antenna-port surge protection; 6 kA or 6 kV Ethernet-port surge protection"
        ),
        "wireless_security": t(
            "WEP; WPA/WPA2-PSK; WPA3-SAE; WPA/WPA2-PPSK; "
            "WPA/WPA2/WPA3-802.1X; WAPI; WIDS/WIPS"
        ),
    }


PRODUCTS = {
    "AirEngine 5760-51": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/f857046ba4844cb0aa6eb510c3b61e83/M3T1A590N1104878761918931174/Huawei%20AirEngine%205760-51%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet, pp. 2-12",
        "title": "Huawei AirEngine 5760-51 official product datasheet",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1150, "Maximum with RTU license; 575 Mbps in the default 2x2 mode"),
            "rate_5g_mbps": n(4800),
            "mimo_2g": t("2x2:2 default; 4x4:4 with RTU license"),
            "mimo_5g": t("4x4:4; triple-radio 2x2:2 + 2x2:2 also supported"),
            "total_spatial_streams": n(8, "Maximum with RTU license; six spatial streams by default"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1152, "Maximum in triple-radio mode; 1024 in dual-radio mode"),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t(
                "1 x 100M/1G/2.5G/5GE PoE-in; 1 x 10/100/1000BASE-T; "
                "USB; built-in BLE 5.2; built-in IoT slots"
            ),
            "power_method": t("42.5-57 V DC or IEEE 802.3at/bt PoE"),
            "max_power_consumption_w": n(28.8, "Maximum in 802.3bt RTU mode; excluding USB and IoT"),
            "dimensions_mm": t("Ø220 x 51 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in dual-band smart antenna array"),
            "antenna_gain_dbi": t("2.4 GHz: 4.5 dBi; 5 GHz: 5.5 dBi (single-antenna peak gain)"),
            "centralized_management": t(
                "Huawei WLAN AC in Fit mode; local web management in Fat mode; "
                "Huawei cloud management platform"
            ),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
                "WPA/WPA2 and WPA2/WPA3 mixed modes; WIDS/WIPS"
            ),
        },
    },
    "AirEngine 5761R-11": {
        "url": OUTDOOR_SOURCE,
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5761R-11 official product specifications",
        "values": {
            **outdoor_common(17.7, "Built-in directional smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 11 dBi"),
        },
    },
    "AirEngine 5761R-11E": {
        "url": OUTDOOR_SOURCE,
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5761R-11E official product specifications",
        "values": {
            **outdoor_common(19.6, "External antennas"),
            "supported_bands": t("2.4 GHz + 5 GHz, or dual 5 GHz"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine high-density and outdoor AP specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
