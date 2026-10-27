from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DATASHEET = "https://download.zyxel.com/PoE12-30W/datasheet/PoE12-30W_7.pdf"
MG108_DATASHEET = "https://download.zyxel.com/MG-108/datasheet/MG-108_4.pdf"
DESKTOP_GUIDE = "https://www.zyxel.com/library/assets/tech-library/product-guide/pg_desktop_switch_2021.pdf"


PRODUCTS = {
    "PoE12-30W": {
        "url": DATASHEET,
        "page": "p. 3, Specifications; PoE12-30W column",
        "title": "Zyxel PoE12-30W / PoE12-60W / PoE12-90W Data Sheet",
        "values": {
            "accessory_interface_type": t(
                "1 x 100M/1G/2.5G RJ45 data input + 1 x 100M/1G/2.5G RJ45 power/data output"
            ),
            "accessory_data_rate_gbps": n(2.5),
            "accessory_input_power": t("100-240 V AC, 1.0 A, 50/60 Hz"),
            "accessory_output_power": t("Up to 30 W PoE output"),
            "accessory_poe_standard": t("IEEE 802.3at PoE+"),
            "accessory_power_w": n(30),
            "max_power_consumption_w": n(
                34.9, "Maximum AC power consumption, including 30 W PoE output"
            ),
            "operating_temperature_c": t("-10 to 45 °C"),
            "dimensions_mm": t("140 x 45.5 x 30 mm (W x D x H)"),
        },
    },
    "PoE12-60W": {
        "url": DATASHEET,
        "page": "p. 3, Specifications; PoE12-60W column",
        "title": "Zyxel PoE12-30W / PoE12-60W / PoE12-90W Data Sheet",
        "values": {
            "accessory_interface_type": t(
                "1 x 100M/1G/2.5G/5G/10G RJ45 data input + "
                "1 x 100M/1G/2.5G/5G/10G RJ45 power/data output",
                "10GbE requires Cat 6a or higher cable and is supported up to 30 m",
            ),
            "accessory_data_rate_gbps": n(
                10, "10GbE requires Cat 6a or higher cable and is supported up to 30 m"
            ),
            "accessory_input_power": t("100-240 V AC, 2.0 A, 50/60 Hz"),
            "accessory_output_power": t("Up to 60 W PoE output"),
            "accessory_poe_standard": t("IEEE 802.3bt PoE++ (60 W)"),
            "accessory_power_w": n(60),
            "max_power_consumption_w": n(
                74.7, "Maximum AC power consumption, including 60 W PoE output"
            ),
            "operating_temperature_c": t("-10 to 40 °C"),
            "dimensions_mm": t("140 x 65 x 38.5 mm (W x D x H)"),
        },
    },
    "PoE12-90W": {
        "url": DATASHEET,
        "page": "p. 3, Specifications; PoE12-90W column",
        "title": "Zyxel PoE12-30W / PoE12-60W / PoE12-90W Data Sheet",
        "values": {
            "accessory_interface_type": t(
                "1 x 100M/1G/2.5G/5G/10G RJ45 data input + "
                "1 x 100M/1G/2.5G/5G/10G RJ45 power/data output"
            ),
            "accessory_data_rate_gbps": n(10),
            "accessory_input_power": t("100-240 V AC, 2.0 A, 50/60 Hz"),
            "accessory_output_power": t("Up to 90 W PoE output"),
            "accessory_poe_standard": t("IEEE 802.3bt PoE++ (90 W)"),
            "accessory_power_w": n(90),
            "max_power_consumption_w": n(
                101.88, "Maximum AC power consumption, including 90 W PoE output"
            ),
            "operating_temperature_c": t("-10 to 40 °C"),
            "dimensions_mm": t("196.25 x 80 x 39.8 mm (W x D x H)"),
        },
    },
    "MG-108": {
        "url": MG108_DATASHEET,
        "page": "p. 3, Specifications; MG-108 column",
        "title": "Zyxel MG100 Series Data Sheet",
        "values": {
            "max_power_consumption_w": n(12.24),
        },
    },
    "DAC10G-1M": {
        "url": DESKTOP_GUIDE,
        "page": "p. 14, Direct Attached Cable 10G Series DAC10G table",
        "title": "Zyxel Desktop Switch Product Guide 2021",
        "values": {
            "dimensions_mm": t("14 x 58 x 11 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 70 °C"),
        },
    },
    "DAC10G-3M": {
        "url": DESKTOP_GUIDE,
        "page": "p. 14, Direct Attached Cable 10G Series DAC10G table",
        "title": "Zyxel Desktop Switch Product Guide 2021",
        "values": {
            "dimensions_mm": t("14 x 58 x 11 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 70 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified Zyxel PoE injector, MG-108, and DAC specifications."
    products = PRODUCTS
    document_version = "Official Zyxel data sheets and product guide; accessed 2026-10-23"
    brand_name = "Zyxel"
