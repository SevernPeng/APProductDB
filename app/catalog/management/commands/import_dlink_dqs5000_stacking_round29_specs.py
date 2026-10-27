from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


SOURCE_URL = (
    "https://www.dlink.com/en/-/media/business_products/dqs/dqs-5000-series/"
    "datasheet/5000-seriesa1datasheetv106ww.pdf"
)


NO_STACK_VALUES = {
    "stacking": t(
        "Not supported",
        "Official hardware and feature inventory lists no stacking function or stacking ports",
    ),
    "stacking_units": n(1, "Standalone switch; maximum stack size is one unit"),
    "stacking_bandwidth_gbps": n(0, "No stacking fabric or stacking ports"),
}


PRODUCTS = {
    model: {
        "url": SOURCE_URL,
        "page": "Technical Specifications and complete feature inventory",
        "title": "D-Link 5000 Series Data Center Switches Datasheet v1.06",
        "values": NO_STACK_VALUES,
    }
    for model in ("DQS-5000-32Q28", "DQS-5000-54SQ28")
}


class Command(VerifiedImportCommand):
    help = "Record the non-stackable design of D-Link DQS-5000 data-center switches."
    products = PRODUCTS
    document_version = "D-Link 5000 Series datasheet v1.06 (current official copy); accessed 2026-10-27"
    brand_name = "D-Link"
