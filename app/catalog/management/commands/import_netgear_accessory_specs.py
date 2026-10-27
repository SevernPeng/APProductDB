from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


AGM_GUIDE = "https://www.downloads.netgear.com/files/GDC/AGM731F/AGM731F_AGM732F_IG_EN.pdf"
M4300_DS = "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4300.pdf"
XS_COMPAT = "https://kb.netgear.com/000049006/What-NETGEAR-SFP-and-SFP-modules-can-I-use-in-NETGEAR-XS505M-and-XS508M-Switches"


PRODUCTS = {
    "AGM731F": {
        "url": AGM_GUIDE,
        "page": "technical specifications",
        "title": "NETGEAR AGM731F/AGM732F SFP 1G Fiber Module Installation Guide",
        "values": {
            "accessory_interface_type": t("SFP (1000BASE-SX)"),
            "accessory_connector_type": t("LC duplex"),
            "accessory_data_rate_gbps": n(1),
            "accessory_fiber_mode": t("Multimode (62.5/125 µm or 50/125 µm)"),
            "accessory_max_distance_km": n(0.55, "Up to 550 m on OM2/OM3; 275 m on OM1"),
            "accessory_wavelength_nm": n(850),
            "dimensions_mm": t("56.8 x 13.6 x 8.6 mm (D x W x H)"),
            "operating_temperature_c": t("-5 to 70 °C case temperature"),
            "max_power_consumption_w": n(1.1),
            "accessory_compatibility": t("NETGEAR managed switches with a supported SFP module slot"),
        },
    },
    "AGM732F": {
        "url": AGM_GUIDE,
        "page": "technical specifications",
        "title": "NETGEAR AGM731F/AGM732F SFP 1G Fiber Module Installation Guide",
        "values": {
            "accessory_interface_type": t("SFP (1000BASE-LX)"),
            "accessory_connector_type": t("LC duplex"),
            "accessory_data_rate_gbps": n(1),
            "accessory_fiber_mode": t("Single-mode 9/125 µm"),
            "accessory_max_distance_km": n(10),
            "accessory_wavelength_nm": n(1310),
            "dimensions_mm": t("57.4 x 13.4 x 8.5 mm (D x W x H)"),
            "operating_temperature_c": t("-5 to 70 °C case temperature"),
            "max_power_consumption_w": n(1.1),
            "accessory_compatibility": t("NETGEAR managed switches with a supported SFP module slot"),
        },
    },
    "AGM734": {
        "url": M4300_DS,
        "page": "GBIC SFP and SFP+ optics / ordering information",
        "title": "NETGEAR M4300 Series Data Sheet",
        "values": {
            "accessory_interface_type": t("SFP (1000BASE-T)"),
            "accessory_connector_type": t("RJ45"),
            "accessory_data_rate_gbps": n(1),
            "accessory_fiber_mode": t("Copper (1000BASE-T)"),
            "accessory_wavelength_nm": na("Copper 1000BASE-T module; optical wavelength is not applicable"),
            "accessory_compatibility": t("NETGEAR M4300 models with a supported SFP/SFP+ interface"),
        },
    },
    "AXC761": {
        "url": XS_COMPAT,
        "page": "supported module table",
        "title": "NETGEAR XS505M and XS508M SFP/SFP+ Module Compatibility",
        "values": {
            "accessory_interface_type": t("SFP+ passive direct-attach copper cable"),
            "accessory_data_rate_gbps": n(10),
            "accessory_cable_length_m": n(1),
            "accessory_compatibility": t("NETGEAR switches with supported SFP+ DAC ports, including XS505M, XS508M and XS508Mv2"),
        },
    },
    "AXC763": {
        "url": XS_COMPAT,
        "page": "supported module table",
        "title": "NETGEAR XS505M and XS508M SFP/SFP+ Module Compatibility",
        "values": {
            "accessory_interface_type": t("SFP+ passive direct-attach copper cable"),
            "accessory_data_rate_gbps": n(10),
            "accessory_cable_length_m": n(3),
            "accessory_compatibility": t("NETGEAR switches with supported SFP+ DAC ports, including XS505M, XS508M and XS508Mv2"),
        },
    },
    "AXM761": {
        "url": "https://www.downloads.netgear.com/files/AXM761_IGprt_10July09.pdf",
        "page": "technical specifications",
        "title": "NETGEAR AXM761 10 Gigabit Ethernet SFP+ Module Installation Guide",
        "values": {
            "accessory_interface_type": t("SFP+ (10GBASE-SR)"),
            "accessory_connector_type": t("LC duplex"),
            "accessory_data_rate_gbps": n(10),
            "accessory_fiber_mode": t("Multimode 50/125 µm or 62.5/125 µm"),
            "accessory_max_distance_km": n(0.3, "2-300 m on 50/125 µm MMF; 2-33 m on 62.5/125 µm MMF"),
            "accessory_wavelength_nm": n(850),
            "dimensions_mm": t("55.7 x 13.7 x 11.9 mm (D x W x H)"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1, "Less than 1.0 W"),
            "accessory_compatibility": t("NETGEAR managed switches with a supported SFP+ module slot"),
        },
    },
    "AXM762": {
        "url": "https://www.downloads.netgear.com/files/GDC/AXM762/AXM762_IG_EN.pdf",
        "page": "technical specifications",
        "title": "NETGEAR AXM762 10 Gigabit Ethernet SFP+ Module Installation Guide",
        "values": {
            "accessory_interface_type": t("SFP+ (10GBASE-LR)"),
            "accessory_connector_type": t("LC duplex"),
            "accessory_data_rate_gbps": n(10),
            "accessory_fiber_mode": t("Single-mode 9/125 µm"),
            "accessory_max_distance_km": n(10, "2 m to 10 km"),
            "accessory_wavelength_nm": n(1310),
            "dimensions_mm": t("55.7 x 13.7 x 11.9 mm (D x W x H)"),
            "operating_temperature_c": t("0 to 70 °C"),
            "max_power_consumption_w": n(1.5, "Less than 1.5 W"),
            "accessory_compatibility": t("NETGEAR managed switches with a supported SFP+ module slot"),
        },
    },
    "AXM765": {
        "url": "https://www.netgear.com/ca-en/business/wired/switches/accessories/axm765/",
        "page": "current AXM765v2 product features and technical specifications",
        "title": "NETGEAR AXM765v2 10GBASE-T SFP+ Transceiver Product Page",
        "values": {
            "accessory_interface_type": t("SFP+/SFP28 (10GBASE-T), AXM765v2"),
            "accessory_connector_type": t("RJ45"),
            "accessory_data_rate_gbps": n(10),
            "accessory_fiber_mode": t("Copper (10GBASE-T)"),
            "accessory_max_distance_km": n(0.08, "Up to 80 m with CAT6a or CAT7"),
            "accessory_wavelength_nm": na("Copper 10GBASE-T module; optical wavelength is not applicable"),
            "accessory_compatibility": t("M4250, M4300 and M4500 managed switches with supported SFP+ or SFP28 interfaces"),
        },
    },
    "APS600Wv3": {
        "url": "https://www.netgear.com/business/wired/switches/accessories/aps600wv3/",
        "page": "current product specifications",
        "title": "NETGEAR APS600Wv3 Power Supply Unit Product Page",
        "values": {
            "accessory_input_power": t("110-240 V AC via C14 connector"),
            "accessory_output_power": t("Up to 600 W at 110/220 V AC input"),
            "accessory_power_w": n(600),
            "dimensions_mm": t("73.5 x 193.8 x 39 mm (W x D x H)"),
            "accessory_compatibility": t(
                "M4350-36X4V (XSM4340CV), M4350-24X8F8V (XSM4340V), "
                "M4350-32F8V (XSM4340FV), M4350-16V4C (VSM4320C), and M4350-40X4C (XSM4344C)"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR optical, DAC, and power-supply accessory specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR product pages, guides, datasheets, and support article; accessed 2026-10-20"
    brand_name = "NETGEAR"
