from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.html"


COMMON = {
    "accessory_compatibility": t(
        "Cisco switches, routers and appliances with a compatible 1GbE SFP port; exact platform and "
        "software support must be checked in the current Cisco Transceiver Module Group compatibility matrix"
    ),
    "accessory_data_rate_gbps": n(1, "1 Gigabit Ethernet SFP"),
    "dimensions_mm": t("8.5 x 13.4 x 56.5 mm (H x W x D)"),
    "max_power_consumption_w": n(1, "Cisco 1GbE SFP modules typically consume up to 1 W per port"),
}


def values(**kwargs):
    return {**COMMON, **kwargs}


PRODUCTS = {
    "GLC-BX-D": {
        "url": URL,
        "page": "1000BASE-BX10 section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("1000BASE-BX10-D bidirectional SFP with DOM"),
            accessory_max_distance_km=n(10, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1490, "Transmit wavelength; receives at 1310 nm"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "GLC-BX-U": {
        "url": URL,
        "page": "1000BASE-BX10 section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("1000BASE-BX10-U bidirectional SFP with DOM"),
            accessory_max_distance_km=n(10, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1310, "Transmit wavelength; receives at 1490 nm"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "GLC-BX40-D-I": {
        "url": URL,
        "page": "1000BASE-BX40 section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("1000BASE-BX40-D industrial bidirectional SFP with DOM"),
            accessory_max_distance_km=n(40, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1550, "Nominal transmit wavelength; receives around 1310 nm"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "GLC-BX40-U-I": {
        "url": URL,
        "page": "1000BASE-BX40 section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("1000BASE-BX40-U industrial bidirectional SFP with DOM"),
            accessory_max_distance_km=n(40, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1310, "Nominal transmit wavelength; receives around 1490/1550 nm"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "GLC-LH-SMD": {
        "url": URL,
        "page": "1000BASE-LX/LH section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("G.652 SMF or MMF with mode-conditioning patch cord"),
            accessory_interface_type=t("1000BASE-LX/LH SFP with DOM"),
            accessory_max_distance_km=n(10, "Up to 10 km on SMF; up to 550 m on MMF"),
            accessory_wavelength_nm=n(1310, "Nominal wavelength"),
            operating_temperature_c=t("-5 to 85 °C (extended temperature range)"),
        ),
    },
    "GLC-LX-SM-RGD": {
        "url": URL,
        "page": "1000BASE-LX/LH section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("G.652 SMF or MMF with mode-conditioning patch cord"),
            accessory_interface_type=t("Rugged 1000BASE-LX/LH SFP with DOM"),
            accessory_max_distance_km=n(10, "Up to 10 km on SMF; up to 550 m on MMF"),
            accessory_wavelength_nm=n(1310, "Nominal wavelength"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "GLC-SX-MM-RGD": {
        "url": URL,
        "page": "1000BASE-SX section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("Multimode fiber (OM1/OM2/OM3/OM4/OM5)"),
            accessory_interface_type=t("Rugged 1000BASE-SX SFP with DOM"),
            accessory_max_distance_km=n(1, "Up to 1 km on laser-optimized OM3/OM4/OM5; 550 m on OM2"),
            accessory_wavelength_nm=n(850, "Nominal wavelength"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "GLC-SX-MMD": {
        "url": URL,
        "page": "1000BASE-SX section and Tables 2-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("Multimode fiber (OM1/OM2/OM3/OM4/OM5)"),
            accessory_interface_type=t("1000BASE-SX SFP with DOM"),
            accessory_max_distance_km=n(1, "Up to 1 km on laser-optimized OM3/OM4/OM5; 550 m on OM2"),
            accessory_wavelength_nm=n(850, "Nominal wavelength"),
            operating_temperature_c=t("-5 to 85 °C (extended temperature range)"),
        ),
    },
    "GLC-TE": {
        "url": URL,
        "page": "1000BASE-T section and Tables 4-5; current official data sheet",
        "title": "Cisco SFP Modules for Gigabit Ethernet Applications Data Sheet",
        "values": values(
            accessory_connector_type=t("RJ-45"),
            accessory_fiber_mode=t("Copper, Category 5e or better UTP"),
            accessory_interface_type=t("10/100/1000BASE-T copper SFP"),
            accessory_max_distance_km=n(0.1, "Maximum 100 m copper link"),
            operating_temperature_c=t("-5 to 85 °C (extended temperature range)"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco 1GbE SFP transceiver specifications."
    products = PRODUCTS
    document_version = "Cisco 1GbE SFP data sheet, current edition; accessed 2026-10-16"
    brand_name = "Cisco"
