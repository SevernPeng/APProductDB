from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


URL_10G = "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/data_sheet_c78-455693.html"
URL_25G = "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/datasheet-c78-736950.html"
URL_100G = "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/datasheet-c78-736282.html"


def compatibility(rate):
    return t(
        f"Cisco switches and routers with a compatible {rate} port; exact platform and software support "
        "must be checked in the current Cisco Transceiver Module Group compatibility matrix"
    )


def sfp10(**kwargs):
    return {
        "accessory_compatibility": compatibility("10GbE SFP+"),
        "accessory_data_rate_gbps": n(10, "10 Gigabit Ethernet"),
        "dimensions_mm": t("8.5 x 13.4 x 56.5 mm (H x W x D)"),
        **kwargs,
    }


def sfp25(rate=25, **kwargs):
    return {
        "accessory_compatibility": compatibility("10/25GbE SFP28" if rate == 25 else "25GbE SFP28"),
        "accessory_data_rate_gbps": n(rate, "Maximum supported Ethernet line rate"),
        "dimensions_mm": t("SFP28 pluggable form factor, approximately 8.5 x 13.4 x 56.5 mm (H x W x D)"),
        **kwargs,
    }


def qsfp100(**kwargs):
    return {
        "accessory_compatibility": compatibility("100GbE QSFP28"),
        "accessory_data_rate_gbps": n(100, "100 Gigabit Ethernet"),
        "dimensions_mm": t("13.5 x 18.4 x 72.4 mm maximum connector-module dimensions (H x W x D)"),
        **kwargs,
    }


PRODUCTS = {
    "SFP-10G-SR": {
        "url": URL_10G,
        "page": "10GBASE-SR section and Tables 3, 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("Multimode fiber (FDDI/OM1/OM2/OM3/OM4/OM5)"),
            accessory_interface_type=t("10GBASE-SR SFP+ optical transceiver with DOM"),
            accessory_max_distance_km=n(0.4, "Up to 400 m on OM4/OM5; 300 m on OM3"),
            accessory_wavelength_nm=n(850, "Nominal wavelength"),
            max_power_consumption_w=n(1, "Maximum module power consumption"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-10G-LR": {
        "url": URL_10G,
        "page": "10GBASE-LR section and Tables 3, 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("G.652 single-mode fiber"),
            accessory_interface_type=t("10GBASE-LR SFP+ optical transceiver with DOM"),
            accessory_max_distance_km=n(10, "Maximum link distance on G.652 SMF"),
            accessory_wavelength_nm=n(1310, "Nominal wavelength"),
            max_power_consumption_w=n(1, "Maximum module power consumption"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-10G-BXD-I": {
        "url": URL_10G,
        "page": "10GBASE-BX section and Tables 3, 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("10GBASE-BX-D industrial bidirectional SFP+ with DOM"),
            accessory_max_distance_km=n(10, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1330, "Transmit wavelength; receives at 1270 nm"),
            max_power_consumption_w=n(1, "Maximum module power consumption"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "SFP-10G-BXU-I": {
        "url": URL_10G,
        "page": "10GBASE-BX section and Tables 3, 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_connector_type=t("Simplex LC/PC"),
            accessory_fiber_mode=t("Single-strand G.652 single-mode fiber"),
            accessory_interface_type=t("10GBASE-BX-U industrial bidirectional SFP+ with DOM"),
            accessory_max_distance_km=n(10, "Maximum link distance on one strand of G.652 SMF"),
            accessory_wavelength_nm=n(1270, "Transmit wavelength; receives at 1330 nm"),
            max_power_consumption_w=n(1, "Maximum module power consumption"),
            operating_temperature_c=t("-40 to 85 °C (industrial temperature range)"),
        ),
    },
    "SFP-10G-T-X": {
        "url": URL_10G,
        "page": "SFP-10G-T-X section and Tables 1, 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_connector_type=t("RJ-45"),
            accessory_fiber_mode=t("Copper: Cat6A/Cat7 for 10G; Cat5e or better for 100M/1G"),
            accessory_interface_type=t("100M/1G/10GBASE-T copper SFP+ transceiver"),
            accessory_max_distance_km=n(0.03, "Up to 30 m at 10Gbps; up to 100 m at 100M/1Gbps"),
            accessory_wavelength_nm=na("Not applicable to a copper transceiver"),
            max_power_consumption_w=n(2.5, "Maximum at 10Gbps"),
            operating_temperature_c=t("-5 to 85 °C (extended temperature range)"),
        ),
    },
    "SFP-H10GB-CU1M": {
        "url": URL_10G,
        "page": "Table 3 and Tables 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_cable_length_m=n(1, "Fixed cable length"),
            accessory_connector_type=t("SFP+ to SFP+"),
            accessory_fiber_mode=t("Passive 30-AWG Twinax copper"),
            accessory_interface_type=t("10GBASE-CU passive direct-attach cable"),
            accessory_max_distance_km=n(0.001, "Fixed 1 m cable"),
            accessory_wavelength_nm=na("Not applicable to a passive copper direct-attach cable"),
            max_power_consumption_w=n(0.1, "Maximum power consumption per cable end"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-H10GB-CU3M": {
        "url": URL_10G,
        "page": "Table 3 and Tables 7-9; current official data sheet",
        "title": "Cisco 10GBASE SFP+ Modules Data Sheet",
        "values": sfp10(
            accessory_cable_length_m=n(3, "Fixed cable length"),
            accessory_connector_type=t("SFP+ to SFP+"),
            accessory_fiber_mode=t("Passive 30-AWG Twinax copper"),
            accessory_interface_type=t("10GBASE-CU passive direct-attach cable"),
            accessory_max_distance_km=n(0.003, "Fixed 3 m cable"),
            accessory_wavelength_nm=na("Not applicable to a passive copper direct-attach cable"),
            max_power_consumption_w=n(0.1, "Maximum power consumption per cable end"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-25G-SR-S": {
        "url": URL_25G,
        "page": "25GBASE-SR section and Tables 2, 3 and 5; current official data sheet",
        "title": "Cisco 25GBASE SFP28 Modules Data Sheet",
        "values": sfp25(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("Multimode fiber (OM3/OM4/OM5)"),
            accessory_interface_type=t("25GBASE-SR SFP28 optical transceiver; RS-FEC required"),
            accessory_max_distance_km=n(0.1, "70 m on OM3; 100 m on OM4/OM5"),
            accessory_wavelength_nm=n(850, "Nominal wavelength"),
            max_power_consumption_w=n(1.2, "Maximum module power consumption"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-10/25G-LR-S": {
        "url": URL_25G,
        "page": "10/25GBASE-LR section and Tables 2, 3 and 5; current official data sheet",
        "title": "Cisco 25GBASE SFP28 Modules Data Sheet",
        "values": sfp25(
            accessory_connector_type=t("Duplex LC/PC"),
            accessory_fiber_mode=t("G.652 single-mode fiber"),
            accessory_interface_type=t("Dual-rate 10/25GBASE-LR SFP28; RS-FEC required at 25G"),
            accessory_max_distance_km=n(10, "Maximum standard link distance at 10G or 25G"),
            accessory_wavelength_nm=n(1310, "Nominal wavelength"),
            max_power_consumption_w=n(1.3, "Maximum module power consumption"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "SFP-H25G-CU1M": {
        "url": URL_25G,
        "page": "25G copper-cable section and Tables 2 and 5; current official data sheet",
        "title": "Cisco 25GBASE SFP28 Modules Data Sheet",
        "values": sfp25(
            accessory_cable_length_m=n(1, "Fixed cable length"),
            accessory_connector_type=t("SFP28 to SFP28"),
            accessory_fiber_mode=t("Passive direct-attach copper"),
            accessory_interface_type=t("25GBASE-CR1 passive direct-attach cable; no FEC required at 1 m"),
            accessory_max_distance_km=n(0.001, "Fixed 1 m cable"),
            accessory_wavelength_nm=na("Not applicable to a passive copper direct-attach cable"),
            max_power_consumption_w=n(0.1, "Maximum power consumption per cable end"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "QSFP-100G-SR4-S": {
        "url": URL_100G,
        "page": "QSFP-100G-SR4-S section and Tables 1, 3, 4 and 7; updated 2026-02-23",
        "title": "Cisco 100GBASE QSFP-100G Modules Data Sheet",
        "values": qsfp100(
            accessory_connector_type=t("MPO-12 (12 fibers)"),
            accessory_fiber_mode=t("Parallel multimode fiber (OM3/OM4/OM5)"),
            accessory_interface_type=t("100GBASE-SR4 QSFP28 optical transceiver"),
            accessory_max_distance_km=n(0.1, "70 m on OM3; 100 m on OM4/OM5"),
            accessory_wavelength_nm=n(850, "Nominal wavelength"),
            max_power_consumption_w=n(3.5, "Maximum module power consumption"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
    "QSFP-100G-CU1M": {
        "url": URL_100G,
        "page": "Table 3, DAC physical characteristics and Table 7; updated 2026-02-23",
        "title": "Cisco 100GBASE QSFP-100G Modules Data Sheet",
        "values": qsfp100(
            accessory_cable_length_m=n(1, "Fixed cable length"),
            accessory_connector_type=t("QSFP28 to QSFP28"),
            accessory_fiber_mode=t("Passive direct-attach copper"),
            accessory_interface_type=t("100GBASE-CR4 passive direct-attach cable"),
            accessory_max_distance_km=n(0.001, "Fixed 1 m cable"),
            accessory_wavelength_nm=na("Not applicable to a passive copper direct-attach cable"),
            max_power_consumption_w=n(1.5, "Maximum power consumption per cable end"),
            operating_temperature_c=t("0 to 70 °C (commercial temperature range)"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco 10G, 25G and 100G transceiver and DAC specifications."
    products = PRODUCTS
    document_version = "Cisco 10G/25G/100G transceiver data sheets, current editions; accessed 2026-10-16"
    brand_name = "Cisco"
