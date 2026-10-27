from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DATASHEET = (
    "https://www.dlink.com/en/-/media/business_products/dms/dms-1100-10tp/"
    "datasheet/dms1100seriesa1datasheetv120ww.pdf"
)


PRODUCTS = {
    "DMS-1100-10TP": {
        "url": DATASHEET,
        "page": "Technical specifications, PoE and physical/environmental tables",
        "title": "D-Link DMS-1100 Series Datasheet v1.20WW",
        "values": {
            "poe_ports": n(8, "PoE ports: Ports 1 to 8"),
            "fan_design": t("1 smart fan", "Ventilation: 1 smart fan"),
        },
    },
    "DMS-1100-10TS": {
        "url": DATASHEET,
        "page": "Technical specifications, physical/environmental table",
        "title": "D-Link DMS-1100 Series Datasheet v1.20WW",
        "values": {
            "fan_design": t("1 smart fan", "Ventilation: 1 smart fan"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact D-Link DMS-1100 PoE-port and cooling specifications."
    products = PRODUCTS
    document_version = "Official DMS-1100 Series datasheet v1.20WW; accessed 2026-10-23"
    brand_name = "D-Link"
