from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    t,
)


URL = (
    "https://arubanetworking.hpe.com/techdocs/AOS-Switch/16.11/"
    "Aruba%202540%20Advanced%20Traffic%20Management%20Guide%20for%20AOS-S%2016.11.pdf"
)


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Configuring VLANs > The number of VLANs allowed on a switch",
        "title": "Aruba 2540 Advanced Traffic Management Guide for AOS-S 16.11",
        "values": {
            "ip_interface_capacity": t(
                "512 IP VLAN interfaces",
                "IP VLAN: 512 total, with up to 512 IPv4 and 512 IPv6",
            ),
        },
    }
    for model in (
        "2540 24G 4SFP+ Switch",
        "2540 24G PoE+ 4SFP+ Switch",
        "2540 48G 4SFP+ Switch",
        "2540 48G PoE+ 4SFP+ Switch",
    )
}


class Command(ArubaImportCommand):
    help = "Import the official IP VLAN interface capacity for Aruba 2540 switches."
    products = PRODUCTS
    document_version = "Official AOS-S 16.11 guide; accessed 2026-10-27"
