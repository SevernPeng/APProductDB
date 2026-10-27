from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
)


DIS_SERIES_URL = (
    "https://www.dlink.com/uk/en/-/media/business_products/dis/100g/"
    "dis_100g_series_datasheet_eu_en.pdf"
)
DGS_3000_URL = (
    "https://www2.dlink.com/en/-/media/business_products/dgs/dgs-3000/"
    "datasheet/dgs_3000_datasheet_en.pdf"
)


PRODUCTS = {
    "DIS-100G-5PSW": {
        "url": DIS_SERIES_URL,
        "page": "Technical Specifications, Power Consumption",
        "title": "D-Link DIS-100G Series Datasheet",
        "values": {
            "max_power_consumption_w": n(
                131.57,
                "Maximum: 131.57 W (PoE on); 4.46 W (PoE off)",
            ),
        },
    },
    "DIS-100G-8SW": {
        "url": "https://www.dlink.com/en/products/dis-100g-8sw",
        "page": "Specification, Max Power Consumption",
        "title": "D-Link DIS-100G-8SW Product Page",
        "values": {
            "max_power_consumption_w": n(8.5, "Max Power Consumption: 8.5 W"),
        },
    },
    "DGS-3000-28XMP": {
        "url": DGS_3000_URL,
        "page": "Feature list and Technical Specifications",
        "title": "D-Link DGS-3000 Series Gigabit L2 Managed Switches Datasheet",
        "values": {
            "rip_support": b(False, "Layer 2 managed switch; RIP is not supported"),
            "ospf_support": b(False, "Layer 2 managed switch; OSPF is not supported"),
            "pbr_support": b(False, "Layer 2 managed switch; policy-based routing is not supported"),
            "vrrp_support": b(False, "Layer 2 managed switch; VRRP is not supported"),
            "multicast_routing": b(False, "Layer 2 managed switch; multicast routing is not supported"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Correct D-Link DIS power values and complete DGS-3000-28XMP L2 routing flags."
    products = PRODUCTS
    document_version = "Current official D-Link product page and datasheets; accessed 2026-10-27"
    brand_name = "D-Link"
