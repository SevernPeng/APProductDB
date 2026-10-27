from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    n,
    t,
    u,
)


URL_1G = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-58051440-1C05-4453-8D08-E9C0F3AEAB79.html"
)
URL_10G = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-C1449A69-FEA4-4DA4-AD25-C73A7FB9CF0A.html"
)
URL_25G = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-340399E9-82E3-41C3-A1B0-9A6FBCF83128.html"
)
URL_100G_SR4 = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-32C25B41-E97F-4E41-BB92-0C66029AF945.html"
)
URL_QSFP28_DAC = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-0CE7214C-D5AF-4EF5-9110-1E4B7BC4A280.html"
)
URL_GUIDE_PDF = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/PDF/"
    "AOS-S%20and%20AOS-CX%20Transceiver%20Guide.pdf"
)
URL_1G_COPPER = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-C632255B-0847-4598-BA1B-38C80C90AD1B.html"
)
URL_10G_COPPER = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-2B1D7FEF-84F6-4549-BFA0-AA304E3E1080.html"
)
URL_8360 = (
    "https://www.hpe.com/psnow/downloadDoc/"
    "HPE%20Aruba%20Networking%20CX%208360%20Switch%20Series-a00094643enw.pdf"
    "?deepLink=&form=false&hf=regular&id=a00094643enw.pdf&isFutureVersion=true"
    "&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section="
    "&softrollSection=&ver=15"
)


COMPAT_1G = (
    "Supported Aruba switch models with 1G-capable SFP/SFP+ ports as listed in the "
    "official AOS-S/AOS-CX Transceiver Guide; exact SKU and minimum software vary by series"
)
COMPAT_10G = (
    "Supported Aruba switch models with 10G-capable SFP+/SFP28 ports as listed in the "
    "official AOS-S/AOS-CX Transceiver Guide; exact SKU and minimum software vary by series"
)
COMPAT_25G = (
    "Aruba 5420, 6300/6300L, 6400, 8100, 8325/8325P/8325H, 8360/8360 v2, 8400X, "
    "9300/9300S and 10000 families in the ports and software revisions listed by the guide"
)


PRODUCTS = {
    "J8177D": {
        "url": URL_1G_COPPER,
        "page": "1G SFP copper specifications and compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 1G copper SFP",
        "values": {
            "accessory_data_rate_gbps": n(1, "1G; 100 Mbps on certain supported platforms"),
            "accessory_max_distance_km": n(0.1, "100 m (328.08 ft)"),
            "accessory_connector_type": t("RJ45"),
            "accessory_interface_type": t("1G SFP RJ45 copper transceiver"),
            "accessory_compatibility": t(
                "Supported Aruba 2510/2530/2540/5400R, 5420, 6000, 6100, 6200, 6300/6300L, "
                "8325, 8360 and 10000 switch ports listed by the official guide"
            ),
            "max_power_consumption_w": u(
                "Official transceiver guide does not publish module power; previous 550 W value was unrelated"
            ),
            "accessory_input_power": u(
                "Official transceiver guide does not publish electrical input details"
            ),
        },
    },
    "J4858D": {
        "url": URL_1G,
        "page": "1G SFP optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 1G SFP optics",
        "values": {
            "accessory_max_distance_km": n(0.5, "Product designation: 1G SFP LC SX 500m MMF"),
            "accessory_wavelength_nm": n(850, "Single lane, 850 nm, 1x1G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1, "Required power: 1 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_1G),
        },
    },
    "J4859D": {
        "url": URL_1G,
        "page": "1G SFP optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 1G SFP optics",
        "values": {
            "accessory_max_distance_km": n(10, "10 km over 9/125 SMF"),
            "accessory_wavelength_nm": n(1310, "Single lane, 1310 nm, 1x1G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1, "Required power: 1 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_1G),
        },
    },
    "J9150D": {
        "url": URL_10G,
        "page": "10G SFP+ optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 10G SFP+ optics",
        "values": {
            "accessory_max_distance_km": n(0.3, "Product designation: 10G SFP+ LC SR 300m OM3 MMF"),
            "accessory_wavelength_nm": n(850, "Single lane, 850 nm, 1x10G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1, "Required power: 1 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_10G),
        },
    },
    "J9151E": {
        "url": URL_10G,
        "page": "10G SFP+ optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 10G SFP+ optics",
        "values": {
            "accessory_max_distance_km": n(10, "10 km over 9/125 SMF"),
            "accessory_wavelength_nm": n(1310, "Single lane, 1310 nm, 1x10G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1, "Required power: 1 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_10G),
        },
    },
    "JL484A": {
        "url": URL_25G,
        "page": "25G SFP28 optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 25G SFP28 optics",
        "values": {
            "accessory_max_distance_km": n(0.1, "100 m over OM4 MMF; 70 m over OM3 MMF"),
            "accessory_wavelength_nm": n(850, "Single lane, 850 nm, 1x25G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1.2, "Required power: 1.2 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_25G),
        },
    },
    "JL486A": {
        "url": URL_25G,
        "page": "25G SFP28 optical specifications and switch compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 25G SFP28 optics",
        "values": {
            "accessory_max_distance_km": n(10, "10 km over 9/125 SMF"),
            "accessory_wavelength_nm": n(1310, "Single lane, 1310 nm, 1x25G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1.5, "Required power: 1.5 W"),
            "accessory_connector_type": t("Duplex LC (PC or UPC)"),
            "accessory_compatibility": t(COMPAT_25G),
        },
    },
    "JL309A": {
        "url": URL_100G_SR4,
        "page": "100G QSFP28 SR4 optical specifications and compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 100G SR4 optics",
        "values": {
            "accessory_max_distance_km": n(0.1, "100 m over OM4 MMF; 70 m over OM3 MMF"),
            "accessory_wavelength_nm": n(850, "4 lanes, 850 nm, 4x25G NRZ"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(3.5, "Required power: 3.5 W"),
            "accessory_connector_type": t("MPO12 (PC polished, 8 fibers used; do not use APC)"),
            "accessory_compatibility": t(
                "Aruba 6300, 6400, 8100, 8325/8325P/8325H, 8360/8360 v2 and 8400X "
                "QSFP28 platforms in the ports and software revisions listed by the guide"
            ),
        },
    },
    "JL487A": {
        "url": URL_GUIDE_PDF,
        "page": "Edition 22, pages 156-161, 25G SFP28 DAC specifications and compatibility",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide, edition 22",
        "values": {
            "accessory_cable_length_m": n(0.65, "0.65 m (2.13 ft)"),
            "accessory_connector_type": t("SFP28 to SFP28"),
            "accessory_interface_type": t("25G SFP28 direct attach copper cable"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(0.2, "Required power: 0.1 W per end; 0.2 W total"),
            "accessory_compatibility": t(
                "Aruba 5420, 6300/6300L, 6400, 8325/8325P/8325H, 8360/8360 v2, "
                "8400X, 9300S and 10000 platforms in supported SFP28 ports listed by the guide"
            ),
        },
    },
    "R0Z25A": {
        "url": URL_QSFP28_DAC,
        "page": "100G QSFP28 DAC specifications and compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 100G QSFP28 DACs",
        "values": {
            "accessory_cable_length_m": n(1, "1 m (3.28 ft)"),
            "accessory_connector_type": t("QSFP28 to QSFP28"),
            "accessory_interface_type": t("100G QSFP28 direct attach copper cable"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(0.2, "Required power: 0.1 W per end; 0.2 W total"),
            "accessory_compatibility": t(
                "Supported Aruba 100G QSFP28 switch ports listed in the official transceiver guide; "
                "exact port and minimum software vary by platform"
            ),
        },
    },
    "JL563A": {
        "url": URL_10G_COPPER,
        "page": "10GBASE-T SFP+ copper specifications and compatibility tables",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide - 10GBASE-T SFP+",
        "values": {
            "accessory_data_rate_gbps": n(10, "Operates only at 10G; does not auto-negotiate to 1G"),
            "accessory_max_distance_km": n(0.03, "30 m (98.43 ft) over shielded Cat6A"),
            "accessory_connector_type": t("RJ45"),
            "accessory_interface_type": t("10GBASE-T SFP+ RJ45 copper transceiver"),
            "operating_temperature_c": t("0 to 85 °C"),
            "accessory_compatibility": t(
                "Aruba 5420, 6200, 6300/6300L, 6400, 8100, 8320, selected 8325, 8360 and "
                "8400X ports listed by the official guide; not supported through QSA28"
            ),
            "accessory_input_power": u(
                "Official transceiver guide does not publish electrical input details"
            ),
        },
    },
    "J9281D": {
        "url": URL_8360,
        "page": "QuickSpecs v15 configuration tables, pages 13 and 22",
        "title": "HPE Aruba Networking CX 8360 Switch Series QuickSpecs, version 15",
        "values": {
            "accessory_cable_length_m": n(1, "10G SFP+ to SFP+ 1m Direct Attach Copper Cable"),
            "accessory_connector_type": t("SFP+ to SFP+"),
            "accessory_interface_type": t("10G SFP+ direct attach copper cable"),
            "accessory_compatibility": t("Aruba CX 8360 Switch Series"),
        },
    },
    "J9283D": {
        "url": URL_8360,
        "page": "QuickSpecs v15 configuration tables, pages 13 and 22",
        "title": "HPE Aruba Networking CX 8360 Switch Series QuickSpecs, version 15",
        "values": {
            "accessory_connector_type": t("SFP+ to SFP+"),
            "accessory_compatibility": t("Aruba CX 8360 Switch Series"),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified Aruba 1G/10G/25G transceiver and DAC gap specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking transceiver guide/QuickSpecs; accessed 2026-10-22"
