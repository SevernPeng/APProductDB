from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


CRS_URL = "https://help.mikrotik.com/docs/spaces/SWOS/pages/76415036/CRS3xx+and+CSS3xx+series+Manual"
RB260_URL = "https://help.mikrotik.com/docs/spaces/SWOS/pages/76414986/CSS106+RB260+series+Manual"


def crs_item():
    return {
        "url": CRS_URL,
        "page": "CRS3xx/CSS3xx features table and Link section",
        "title": "MikroTik CRS3xx and CSS3xx Series SwOS Manual",
        "values": {
            "jumbo_frame_bytes": n(10218, "Jumbo frame support - 10218 bytes"),
            "vlan_count": n(250, "Up to 250 VLAN entries (limited by SwOS)"),
        },
    }


PRODUCTS = {
    "CRS309-1G-8S+IN": crs_item(),
    "CRS317-1G-16S+RM": crs_item(),
    "CRS326-24S+2Q+RM": crs_item(),
    "CRS328-4C-20S-4S+RM": crs_item(),
    "RB260GSP": {
        "url": RB260_URL,
        "page": "Features, Link, and VLAN/VLANs sections",
        "title": "MikroTik CSS106 (RB260) Series SwOS Manual",
        "values": {
            "jumbo_frame_bytes": n(9198, "Jumbo frame support - 9198 bytes"),
            "vlan_count": n(250, "VLAN table supports up to 250 entries"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import official MikroTik SwOS jumbo-frame and VLAN-table capacities."
    products = PRODUCTS
    document_version = "Current official MikroTik SwOS manuals; accessed 2026-10-21"
    brand_name = "MikroTik"
