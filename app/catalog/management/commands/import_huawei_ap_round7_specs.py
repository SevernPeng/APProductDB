from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "AirEngine 5776-57T": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/20efce0b1dbf4c109a7f91dbac831e45/M3T1A590N1153303445208482005/Huawei%20AirEngine%205776-56T_AirEngine%205776-57T%20Access%20Points%20Datasheet.pdf",
        "page": "Current official product page and official datasheet",
        "title": "Huawei AirEngine 5776-57T official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(689),
            "rate_5g_mbps": n(1440),
            "rate_6g_mbps": n(5760),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "mimo_6g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(320),
            "max_clients": n(1800),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t(
                "1 x 100M/1G/2.5G/5GE PoE-in; 1 x 10/100/1000BASE-T; USB; BLE 5.2"
            ),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(21.1),
            "dimensions_mm": t("Ø220 x 45 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t(
                "2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 5 dBi (single-antenna peak gain)"
            ),
            "mounting_options": t("Wall or ceiling"),
            "centralized_management": t(
                "Huawei WLAN AC in Fit mode; local Fat mode; Huawei cloud management platform"
            ),
            "mesh_support": b(True),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming"),
            "wireless_security": t(
                "WPA2-Personal/Enterprise; WPA3-Personal/Enterprise; WPA/WPA2 and "
                "WPA2/WPA3 mixed modes; PPSK/DPSK; WAPI; 802.11w PMF; WIDS/WIPS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5776-57T specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product page, datasheet, and 2026 Q1 portfolio; accessed 2026-10-19"
    brand_name = "Huawei"
