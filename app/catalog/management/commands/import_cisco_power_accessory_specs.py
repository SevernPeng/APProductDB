from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL_650 = "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9500/hardware/install/b-c9500-alternate-power-supply-installation-note.html"
URL_INJ6 = "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MA-INJ-6_Meraki_Multigigabit_802.3bt_Power_over_Ethernet_Injector"


PRODUCTS = {
    "C9K-PWR-650WAC-R": {
        "url": URL_650,
        "page": "Technical Specifications and compatibility statement; revised 2024",
        "title": "C9K-PWR-650WAC-R Power Supply Module Installation Note",
        "values": {
            "accessory_compatibility": t(
                "Cisco Catalyst 9500 high-performance models that support the 650 W AC PSU: "
                "C9500-32QC, C9500-48Y4C and C9500-24Y4C"
            ),
            "accessory_input_power": t(
                "90-132 or 180-264 VAC, 47-63 Hz; up to 7.6 A at low line or 3.65 A at high line; 760 VA maximum"
            ),
            "accessory_output_power": t("650 W maximum; 12 VDC main and 12 VDC standby outputs"),
            "accessory_power_w": n(650, "Maximum rated output power per supply"),
        },
    },
    "MA-INJ-6": {
        "url": URL_INJ6,
        "page": "Power, Data, Environmental, Physical Dimensions and Compatibility sections",
        "title": "MA-INJ-6 Meraki Multigigabit 802.3bt Power over Ethernet Injector",
        "values": {
            "accessory_compatibility": t(
                "IEEE 802.3bt/at/af powered devices including supported Cisco Meraki Wi-Fi 6, Wi-Fi 6E and "
                "Wi-Fi 7 access points; official examples include CW9163E, MR36/MR36H, MR44, MR46/MR46E, "
                "MR56, MR57 and MR76"
            ),
            "accessory_data_rate_gbps": n(10, "Supports 10/100/1000/2500/5000/10000 Multigigabit Ethernet"),
            "accessory_input_power": t("100-240 VAC, 50-60 Hz; 2.0 A RMS at 90 VAC or 1.2 A RMS at 240 VAC under maximum load"),
            "accessory_interface_type": t("In-line multigigabit Ethernet PoE injector with data input and data/power output"),
            "accessory_output_power": t("55 VDC, 60 W maximum output; powered-device cable length up to 100 m"),
            "accessory_poe_standard": t("IEEE 802.3bt; backward compatible with IEEE 802.3at and 802.3af"),
            "accessory_power_w": n(60, "Maximum PoE output power"),
            "dimensions_mm": t("163.25 x 65 x 40 mm including mounting ears"),
            "operating_temperature_c": t("-10 to 60 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco C9500 PSU and Meraki MA-INJ-6 specifications."
    products = PRODUCTS
    document_version = "Cisco PSU installation note and Meraki MA-INJ-6 data sheet; accessed 2026-10-16"
    brand_name = "Cisco"
