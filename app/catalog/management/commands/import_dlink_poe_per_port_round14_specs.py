from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "DMS-1100-10TP": {
        "url": (
            "https://www.dlink.com/en/-/media/business_products/dms/dms-1100-10tp/"
            "datasheet/dms1100seriesa1datasheetv120ww.pdf"
        ),
        "page": "PoE and technical specifications",
        "title": "D-Link DMS-1100 Series Datasheet v1.20WW",
        "values": {
            "max_poe_per_port_w": n(30, "Capable of supplying up to 30 W of power per port"),
        },
    },
    "DMS-1250-10SP": {
        "url": (
            "https://www.dlink.com/us/en/-/media/business_products/dms/dms-1250/"
            "datasheet/dms1250seriesdatasheetv103ww.pdf"
        ),
        "page": "PoE and technical specifications, pp. 1 and 3",
        "title": "D-Link DMS-1250 Series Datasheet v1.03WW",
        "values": {
            "max_poe_per_port_w": n(30, "IEEE 802.3af/at (30W)"),
        },
    },
    "DMS-1250-18P": {
        "url": (
            "https://support.dlink.com/resource/products/DMS-1250-Series/"
            "DMS-1250-SERIES_Datasheet_v1.06WW.pdf"
        ),
        "page": "Technical specifications, PoE table",
        "title": "D-Link DMS-1250 Series Datasheet v1.06WW",
        "values": {
            "max_poe_per_port_w": n(90, "IEEE 802.3af/at/bt (90W)"),
        },
    },
    "DMS-1250-28P": {
        "url": (
            "https://support.dlink.com/resource/products/DMS-1250-Series/"
            "DMS-1250-SERIES_Datasheet_v1.06WW.pdf"
        ),
        "page": "Technical specifications, PoE table",
        "title": "D-Link DMS-1250 Series Datasheet v1.06WW",
        "values": {
            "max_poe_per_port_w": n(90, "IEEE 802.3af/at/bt (90W)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact per-port PoE limits for four D-Link multi-gigabit switches."
    products = PRODUCTS
    document_version = "Latest official D-Link datasheets checked 2026-10-23"
    brand_name = "D-Link"
