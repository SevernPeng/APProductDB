from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "DEM-310GT": {
        "url": "https://www2.dlink.com/in/en/products/dem-310gt-sp",
        "page": "Specification table",
        "title": "D-Link DEM-310GT/SP Product Page",
        "values": {
            "accessory_data_rate_gbps": n(1.25, "Data Rate: 1.25 Gbps"),
            "dimensions_mm": t("56 x 13.7 x 8.5 mm", "Dimensions"),
            "operating_temperature_c": t("0 to 70 °C", "Operating temperature"),
        },
    },
    "DMC-1014": {
        "url": (
            "https://www.dlink.com/middle-east/en/products/"
            "dmc-1014-14-slot-standalone-media-converter-chassis"
        ),
        "page": "Product overview",
        "title": "D-Link DMC-1014 Product Page",
        "values": {
            "accessory_compatibility": t(
                "D-Link media converters designed for installation in the DMC-1014 chassis",
                "Mount up to 14 media converters in the specially designed DMC-1014 Media Converter Chassis",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and correct exact D-Link DEM-310GT and DMC-1014 accessory specifications."
    products = PRODUCTS
    document_version = "Official D-Link product pages; accessed 2026-10-23"
    brand_name = "D-Link"
