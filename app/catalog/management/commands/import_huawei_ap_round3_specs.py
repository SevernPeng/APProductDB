from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


def common(rate_5g, max_power, dimensions, power, max_clients, mounting):
    return {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(575),
        "rate_5g_mbps": n(rate_5g),
        "mimo_2g": t("2x2:2 MU-MIMO"),
        "mimo_5g": t("2x2:2 MU-MIMO"),
        "total_spatial_streams": n(4),
        "max_clients": n(max_clients),
        "power_method": t(power),
        "max_power_consumption_w": n(max_power),
        "dimensions_mm": t(dimensions),
        "operating_temperature_c": t("0 to 40 °C"),
        "antenna_type": t("Built-in dual-band co-planar smart antennas"),
        "mounting_options": t(mounting),
    }


PRODUCTS = {
    "AirEngine 5761-12W": {
        "url": "https://e.huawei.com/hu/products/wlan/indoor-access-points/airengine-5761-12w",
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5761-12W official product specifications",
        "values": {
            **common(
                1200,
                13.1,
                "38 x 86 x 160 mm",
                "46-57 V DC or IEEE 802.3af/at PoE",
                1024,
                "Wall or junction box",
            ),
            "ethernet_interfaces": t(
                "1 x Gigabit Ethernet uplink; 4 x Gigabit Ethernet downlink "
                "(one supports PoE out); 2 x pass-through RJ45 (RJ11 compatible)"
            ),
            "poe_output": t("Yes; one Gigabit Ethernet downlink port supports PoE out"),
            "centralized_management": t("Huawei cloud management platform"),
        },
    },
    "AirEngine 5762-12SW": {
        "url": "https://e.huawei.com/en/products/wlan/indoor-access-points/airengine-5762-12sw",
        "page": "Current official product specifications and official product datasheet",
        "title": "Huawei AirEngine 5762-12SW official product specifications",
        "values": {
            **common(
                2400,
                12,
                "86 x 86 x 46 mm",
                "IEEE 802.3af PoE",
                256,
                "Wall or wall plate",
            ),
            "max_channel_width_mhz": n(160),
            "ethernet_interfaces": t(
                "1 x Gigabit Ethernet uplink; 1 x Gigabit Ethernet downlink; "
                "Bluetooth serial interface"
            ),
        },
    },
    "AirEngine 5762-13W": {
        "url": "https://e.huawei.com/au/products/wlan/indoor-access-points/airengine-5762-13w",
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5762-13W official product specifications",
        "values": {
            **common(
                2400,
                12,
                "160 x 86 x 38 mm",
                "12 V DC or IEEE 802.3af/at PoE",
                256,
                "Wall or junction box",
            ),
            "max_channel_width_mhz": n(160),
            "ethernet_interfaces": t(
                "1 x Gigabit Ethernet uplink; 1 x Gigabit Ethernet downlink"
            ),
            "centralized_management": t("Huawei cloud management platform"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine wall-plate AP specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
