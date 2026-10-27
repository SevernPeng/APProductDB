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


def wifi7_common(dimensions, temperature, antenna, ports, power, max_power, management):
    return {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(689),
        "rate_5g_mbps": n(2880),
        "mimo_2g": t("2x2:2 MU-MIMO"),
        "mimo_5g": t("2x2:2 MU-MIMO"),
        "total_spatial_streams": n(4),
        "max_channel_width_mhz": n(160),
        "ethernet_interfaces": t(ports),
        "power_method": t(power),
        "max_power_consumption_w": n(max_power),
        "dimensions_mm": t(dimensions),
        "operating_temperature_c": t(temperature),
        "antenna_type": t(antenna),
        "centralized_management": t(management),
        "mesh_support": b(True),
        "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
        "wireless_security": t(SECURITY),
    }


PRODUCTS = {
    "AirEngine 5773-21": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/3dc3aa631b0e45cd8ad944f9ad9d35d1/M3T1A590N1186036079629922379/Huawei%20AirEngine%205773-21%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, V600R24C10, pp. 2-10",
        "title": "Huawei AirEngine 5773-21 official product datasheet",
        "values": {
            **wifi7_common(
                "Ø180 x 45 mm",
                "-10 to 50 °C",
                "Built-in dual-band smart antennas",
                "1 x 100M/1G/2.5GE PoE-in; USB; BLE 5.4; NearLink SLE 1.0",
                "12 V DC or IEEE 802.3af/at PoE",
                13.6,
                "Huawei WLAN AC in Fit mode or Huawei cloud management platform",
            ),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi (single-antenna peak gain)"),
            "max_ssids": n(15, "Per radio"),
        },
    },
    "AirEngine 5773-23HW": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/4a488a7a12e246439008222ef5763076/M3T1A590N1186036090807701675/Huawei%20AirEngine%205773-23HW%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, V600R25C00, pp. 2-10",
        "title": "Huawei AirEngine 5773-23HW official product datasheet",
        "values": {
            **wifi7_common(
                "160 x 86 x 38 mm",
                "0 to 40 °C",
                "Built-in dual-band smart antennas",
                "1 x 1G/2.5GE BIDI optical uplink with hybrid-cable power; "
                "4 x 10/100/1000BASE-T downlink; USB; BLE 5.2",
                "12 V DC or IEEE 802.3af/at PoE through hybrid-cable Phoenix connector",
                14.2,
                "Huawei WLAN AC in Fit mode; local Fat mode; Huawei cloud management platform",
            ),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 3 dBi (single-antenna peak gain)"),
            "max_clients": n(1200, "600 per radio"),
            "max_ssids": n(15, "Per radio"),
            "poe_output": t("Not supported on the four GE electrical downlink ports"),
        },
    },
    "AirEngine 5773I-21": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/b5ca453b8c2147248721ea4a6bd0f8a0/M3T1A590N1186032552014082174/Huawei%20AirEngine%205773I-21%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, pp. 2-10",
        "title": "Huawei AirEngine 5773I-21 official product datasheet",
        "values": {
            **wifi7_common(
                "270 x 196 x 51 mm",
                "-30 to 60 °C",
                "Built-in omnidirectional antennas",
                "1 x 100M/1G/2.5GE PoE-in; Bluetooth 5.2",
                "IEEE 802.3at PoE",
                18.8,
                "Huawei WLAN AC in Fit mode; local Fat mode; Huawei cloud management platform",
            ),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 7 dBi (single-antenna peak gain)"),
            "max_ssids": n(15, "Per radio"),
            "ip_rating": t("IP65"),
            "lightning_protection_kv": t("6 kA / 6 kV Ethernet-port surge protection"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine Wi-Fi 7 AP specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
