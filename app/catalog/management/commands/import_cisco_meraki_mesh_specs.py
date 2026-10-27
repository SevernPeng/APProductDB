from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
)


URL = "https://documentation.meraki.com/Wireless/Design_and_Configure/Deployment_Guides/Mesh_Deployment_Guide"


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Access Point Capabilities; all Meraki access points support wireless meshing",
        "title": "Cisco Meraki Mesh Deployment Guide (updated 2025-10-21)",
        "values": {
            "mesh_support": b(
                True,
                "Supported in Meraki cloud-managed mode; the Cisco IOS XE feature matrix lists Mesh Mode as unsupported for CW917x",
            )
        },
    }
    for model in (
        "CW9171I",
        "CW9172I",
        "CW9172H",
        "CW9174I",
        "CW9176I",
        "CW9178I",
    )
}


class Command(VerifiedImportCommand):
    help = "Import Cisco CW917x Meraki-mode wireless mesh support."
    products = PRODUCTS
    document_version = "Cisco Meraki Mesh Deployment Guide, updated 2025-10-21; accessed 2026-10-16"
    brand_name = "Cisco"
