from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "AirEngine 5761-21": {
        "url": "https://e.huawei.com/eu/products/wlan/indoor-access-points/airengine-5761-21",
        "page": "Current official product specifications and linked product datasheet",
        "title": "Huawei AirEngine 5761-21 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(4800),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024),
            "ethernet_interfaces": t("1 x 100/1000/2.5GBASE-T PoE-in; 1 x 10/100/1000BASE-T; USB; Bluetooth serial interface"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(17.9, "Excluding USB"),
            "dimensions_mm": t("Ø220 x 50 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in dual-band co-planar smart antennas"),
            "centralized_management": t("Huawei cloud management platform; Fat, Fit, and cloud operating modes"),
            "mounting_options": t("Wall, ceiling, junction box, horizontal pole, or threaded rod"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5761-21 specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product page and datasheet; accessed 2026-10-19"
    brand_name = "Huawei"
