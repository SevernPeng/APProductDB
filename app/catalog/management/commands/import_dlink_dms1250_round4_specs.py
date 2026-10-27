from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://www.dlink.com/us/en/-/media/product-pages/dms/1250-series/dms1250seriesdatasheetv106ww.pdf"


def values(fans):
    return {
        "jumbo_frame_bytes": n(12000, "Jumbo Frame: up to 12,000 bytes"),
        "vlan_count": n(4096, "Supports Virtual LAN (802.1Q) with up to 4K VLAN groups"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
        "acl_security": t(
            "Ingress and time-based ACLs; 802.1X; RADIUS/TACACS+; IP-MAC-port binding; DHCP snooping; D-Link Safeguard Engine"
        ),
        "fan_design": t(fans),
        "power_supply": t("Internal power supply"),
    }


PRODUCTS = {
    "DMS-1250-10S": {
        "url": URL,
        "title": "D-Link DMS-1250 Series Smart Managed Switches Datasheet, version 1.06WW",
        "page": "Series specifications; DMS-1250-10S hardware table",
        "values": values("Fanless"),
    },
    "DMS-1250-10SP": {
        "url": URL,
        "title": "D-Link DMS-1250 Series Smart Managed Switches Datasheet, version 1.06WW",
        "page": "Series specifications; DMS-1250-10SP hardware table",
        "values": values("2 internal fans"),
    },
    "DMS-1250-18P": {
        "url": URL,
        "title": "D-Link DMS-1250 Series Smart Managed Switches Datasheet, version 1.06WW",
        "page": "Series specifications; DMS-1250-18P hardware table",
        "values": values("3 internal fans"),
    },
    "DMS-1250-28": {
        "url": URL,
        "title": "D-Link DMS-1250 Series Smart Managed Switches Datasheet, version 1.06WW",
        "page": "Series specifications; DMS-1250-28 hardware table",
        "values": values("2 internal fans"),
    },
    "DMS-1250-28P": {
        "url": URL,
        "title": "D-Link DMS-1250 Series Smart Managed Switches Datasheet, version 1.06WW",
        "page": "Series specifications; DMS-1250-28P hardware table",
        "values": values("4 internal fans"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import DMS-1250 current series jumbo, VLAN, STP, ACL, cooling, and power specifications."
    products = PRODUCTS
    document_version = "1.06WW; accessed 2026-10-21"
    brand_name = "D-Link"
