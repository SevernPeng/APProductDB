from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "DEM-CB100Q28": {
        "url": "https://www.dlink.com/en/products/dem-cb100q28",
        "page": "Overview and Specifications",
        "title": "D-Link DEM-CB100Q28 Product Page",
        "values": {
            "accessory_fiber_mode": t(
                "Passive copper direct-attach cable",
                "QSFP28 passive direct-attach cable assembly; no optical fiber mode",
            ),
            "accessory_max_distance_km": n(0.001, "Fixed cable length: 1 m (0.001 km)"),
        },
    },
    "DGS-712": {
        "url": "https://www.dlink.com/en/products/dgs-712-1000base-t-copper-sfp-transceiver",
        "page": "Overview and Technical Specifications",
        "title": "D-Link DGS-712 Product Page",
        "values": {
            "accessory_fiber_mode": t(
                "Copper twisted pair",
                "1000BASE-T copper SFP with RJ-45 connector; Cat 5 or above",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Complete copper-medium details for D-Link direct-attach and SFP accessories."
    products = PRODUCTS
    document_version = "Current official D-Link product pages; accessed 2026-10-27"
    brand_name = "D-Link"
