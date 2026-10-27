from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "DEM-S2801SR": {
        "url": (
            "https://support.dlink.com/resource/products/DEM-S2801SR/"
            "DEM-S28%20Series_A1_Datasheet_v1.00%28WW%29.pdf"
        ),
        "page": "Technical specifications table",
        "title": "D-Link DEM-S28 Series Datasheet v1.00WW",
        "values": {
            "accessory_wavelength_nm": n(850, "Wavelength: 850 nm"),
            "dimensions_mm": t("57.3 x 13.7 x 8.5 mm", "Dimensions (L x W x H)"),
            "operating_temperature_c": t("0 to 70 °C", "Operating temperature"),
            "accessory_compatibility": t(
                "SFP28 ports; IEEE 802.3by/802.3cc and MSA compliant",
                "Standards and MSA compliance",
            ),
        },
    },
    "DGS-712": {
        "url": (
            "https://support.dlink.com/resource/products/DGS-712/REVA/"
            "DGS-712_DATASHEET_1.00_EN.PDF"
        ),
        "page": "Product overview and technical specifications",
        "title": "D-Link DGS-712 Datasheet v1.00",
        "values": {
            "dimensions_mm": t("11 x 75 x 11 mm", "Dimensions (W x D x H)"),
            "operating_temperature_c": t("0 to 85 °C", "Operating temperature"),
            "accessory_compatibility": t(
                "Standard SFP interface; host must support SGMII for 10/100/1000 Mbps or SERDES for 1000 Mbps",
                "Host interface requirements stated in the official datasheet",
            ),
        },
    },
    "DEM-CB100Q28": {
        "url": "https://www.dlink.com/en/products/dem-cb100q28",
        "page": "Product description",
        "title": "D-Link DEM-CB100Q28 Product Page",
        "values": {
            "accessory_compatibility": t(
                "D-Link DXS-3610 series 100G QSFP28 ports",
                "Compatible with DXS-3610 series switches",
            ),
        },
    },
    "DMC-1014": {
        "url": (
            "https://www.dlink.com/middle-east/en/products/"
            "dmc-1014-14-slot-standalone-media-converter-chassis"
        ),
        "page": "Technical specifications",
        "title": "D-Link DMC-1014 Product Page",
        "values": {
            "operating_temperature_c": t("-10 to 60 °C", "Operating temperature"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact D-Link accessory optical, physical, environmental, and compatibility specifications."
    products = PRODUCTS
    document_version = "Official D-Link product pages and datasheets; accessed 2026-10-23"
    brand_name = "D-Link"
