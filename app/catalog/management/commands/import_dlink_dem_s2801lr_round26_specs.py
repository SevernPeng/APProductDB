from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "DEM-S2801LR": {
        "url": "https://www.dlink.co.il/mn/products/1/2539.html",
        "page": "General Features and Physical Parameters; order code DEM-S2801LR/A1A",
        "title": "D-Link DEM-S2801LR Official Product Page",
        "values": {
            "accessory_wavelength_nm": n(1310, "TX/RX wavelength: 1310 nm"),
            "operating_temperature_c": t("0 to 70 °C", "Operating temperature: 0° to 70°C"),
            "dimensions_mm": t("57.3 x 13.7 x 8.5 mm", "Dimensions: 57.3 x 13.7 x 8.5 mm"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import official D-Link DEM-S2801LR optical and physical specifications."
    products = PRODUCTS
    document_version = "Official D-Link DEM-S2801LR/A1A product page; accessed 2026-10-27"
    brand_name = "D-Link"
