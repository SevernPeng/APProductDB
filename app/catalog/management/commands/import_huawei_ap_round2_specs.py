from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


def common(rate_5g, max_power, dimensions, power, ports, max_clients=None):
    values = {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(575),
        "rate_5g_mbps": n(rate_5g),
        "mimo_2g": t("2x2:2 MU-MIMO"),
        "mimo_5g": t("2x2:2 MU-MIMO"),
        "total_spatial_streams": n(4),
        "ethernet_interfaces": t(ports),
        "power_method": t(power),
        "max_power_consumption_w": n(max_power),
        "dimensions_mm": t(dimensions),
        "operating_temperature_c": t("-10 to 50 °C"),
        "antenna_type": t("Built-in dual-band co-planar smart antennas"),
        "centralized_management": t("Huawei cloud management platform; Fat, Fit, and cloud operating modes"),
        "mounting_options": t("Wall or ceiling"),
    }
    if rate_5g == 2400:
        values["max_channel_width_mhz"] = n(160)
    if max_clients is not None:
        values["max_clients"] = n(max_clients)
    return values


PRODUCTS = {
    "AirEngine 5761-11": {
        "url": "https://e.huawei.com/eu/products/wlan/indoor-access-points/airengine-5761-11",
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5761-11 official product specifications",
        "values": common(
            1200,
            15.3,
            "Ø220 x 50 mm",
            "12 V DC or IEEE 802.3af/at PoE",
            "1 x Gigabit Ethernet PoE-in; USB; Bluetooth serial interface",
            1024,
        ),
    },
    "AirEngine 5762-10": {
        "url": "https://e.huawei.com/au/products/wlan/indoor-access-points/airengine-5762-10",
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5762-10 official product specifications",
        "values": common(
            2400,
            11.2,
            "Ø180 x 35 mm",
            "12 V DC or IEEE 802.3af PoE",
            "1 x Gigabit Ethernet PoE-in",
        ),
    },
    "AirEngine 5762-12": {
        "url": "https://e.huawei.com/cn/products/wlan/indoor-access-points/airengine-5762-12",
        "page": "Current official product specifications and linked datasheet",
        "title": "Huawei AirEngine 5762-12 official product specifications",
        "values": common(
            2400,
            11,
            "Ø180 x 35 mm",
            "12 V DC or IEEE 802.3af PoE",
            "1 x Gigabit Ethernet PoE-in",
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5761-11 and 5762-10/12 specifications."
    products = PRODUCTS
    document_version = "Current official Huawei product pages and datasheets; accessed 2026-10-19"
    brand_name = "Huawei"
