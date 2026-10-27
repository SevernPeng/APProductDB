from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


GS205_DS = "https://www.downloads.netgear.com/files/GDC/datasheet/en/200-Series_DS.pdf"
GS608_DS = "https://www.netgear.com/images/datasheet/switches/GS605_GS608.pdf"


PRODUCTS = {
    "GS205": {
        "url": GS205_DS,
        "page": "p. 2, Standards",
        "title": "NETGEAR 200 Series Home/Office Ethernet Switches Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x flow control", "802.3x Flow Control"),
        },
    },
    "GS608": {
        "url": GS608_DS,
        "page": "p. 2, Technical Specifications, GS608 column",
        "title": "NETGEAR GS605 and GS608 SOHO Ethernet Switches Data Sheet",
        "values": {
            "max_power_consumption_w": n(
                "3.52", "Power Consumption (Max and Standby): 3.52W/0.57W"
            ),
            "dimensions_mm": t(
                "165 x 93 x 30 mm", "Width x Depth x Height: 165 x 93 x 30 mm"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified NETGEAR GS205 flow control and correct GS608 model-column values."
    products = PRODUCTS
    document_version = "DS-200Series-16Dec20 and D-GS605/GS608-11Jan21; accessed 2026-10-22"
    brand_name = "NETGEAR"
