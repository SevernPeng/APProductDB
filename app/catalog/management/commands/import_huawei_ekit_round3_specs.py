from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "eKit AP371": {
        "url": "https://e.huawei.com/en/documents/products/enterprise-network/6771a6e680a5468b83ffcbbf21ffa97d",
        "page": "Current official product datasheet and official 2026 eKit solution page",
        "title": "Huawei eKitEngine AP371 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(690),
            "rate_5g_mbps": n(2880),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256),
            "max_ssids": n(10, "Per radio"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5GE PoE-in; 1 x USB"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(13.6, "Excluding USB; current official datasheet value"),
            "dimensions_mm": t("Ø180 x 35 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mounting_options": t("Wall or ceiling, including T-rail mounting"),
            "centralized_management": t(
                "Huawei WAC in Fit mode; HUAWEI eKit App, SNC, and Huawei cloud management platform"
            ),
            "mesh_support": b(True, "Mesh is supported in cloud management mode"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei eKit AP371 specifications."
    products = PRODUCTS
    document_version = "Current official Huawei eKit datasheet and 2026 product page; accessed 2026-10-19"
    brand_name = "Huawei"
