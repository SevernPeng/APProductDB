from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PLUS_MANUAL_URL = (
    "https://www.downloads.netgear.com/files/GDC/GS105EV2/"
    "WebManagedSwitches_UM_EN.pdf"
)
WBE_COMPARISON_URL = (
    "https://www.netgear.com/sg/business/wifi/access-points/wbe718/"
)
PR60X_URL = "https://www.downloads.netgear.com/files/GDC/PR60X/PR60X_DS.pdf"


PORT_ISOLATION = b(
    True,
    (
        "Configurable port-based VLANs are supported; the official manual states "
        "that VLAN member ports form an isolated network"
    ),
)


PRODUCTS = {
    "GS105E": {
        "url": PLUS_MANUAL_URL,
        "page": "VLAN overview and Basic port-based VLANs, pp. 29-31",
        "title": "NETGEAR Gigabit Ethernet Plus Switches User Manual",
        "values": {"port_isolation": PORT_ISOLATION},
    },
    "GS108E": {
        "url": PLUS_MANUAL_URL,
        "page": "VLAN overview and Basic port-based VLANs, pp. 29-31",
        "title": "NETGEAR Gigabit Ethernet Plus Switches User Manual",
        "values": {"port_isolation": PORT_ISOLATION},
    },
    "GS116E": {
        "url": PLUS_MANUAL_URL,
        "page": "VLAN overview and Basic port-based VLANs, pp. 29-31",
        "title": "NETGEAR Gigabit Ethernet Plus Switches User Manual",
        "values": {"port_isolation": PORT_ISOLATION},
    },
    "WBE700": {
        "url": WBE_COMPARISON_URL,
        "page": "Current access-point comparison table",
        "title": "NETGEAR WBE718 Official Product Page and Access Point Comparison",
        "values": {
            "max_power_consumption_w": n(
                25,
                "Official comparison entry for WBE700: up to 25 W",
            ),
        },
    },
    "WBE708": {
        "url": WBE_COMPARISON_URL,
        "page": "Current access-point comparison table",
        "title": "NETGEAR WBE718 Official Product Page and Access Point Comparison",
        "values": {
            "max_power_consumption_w": n(
                25,
                "Official comparison entry for WBE708: up to 25 W",
            ),
        },
    },
    "PR60X": {
        "url": PR60X_URL,
        "page": "Hardware and connectivity specifications",
        "title": "NETGEAR PR60X Data Sheet",
        "values": {
            "usb_interfaces": t(
                "No USB interface",
                "The complete official hardware interface inventory contains no USB port",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import remaining verified NETGEAR isolation, power, and interface specifications."
    products = PRODUCTS
    document_version = "Current official NETGEAR pages and manuals; manually verified 2026-10-27"
    brand_name = "NETGEAR"
