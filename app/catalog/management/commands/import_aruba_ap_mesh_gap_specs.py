from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
)


URL = (
    "https://arubanetworking.hpe.com/techdocs/central/2.5.7/content/"
    "aos10x/cfg/aps/mesh-ap-config.htm"
)
TITLE = "HPE Aruba Networking Central - Enterprise Mesh Network with Mesh APs"


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Supported APs table for WPA3-SAE enterprise mesh on all radio bands",
        "title": TITLE,
        "values": {
            "mesh_support": b(
                True,
                f"{source_model} is explicitly listed in the official Enterprise Mesh supported AP table",
            )
        },
    }
    for model, source_model in {
        "AP-503": "AP-503",
        "AP-505": "AP-505",
        "AP-515": "AP-515",
        "AP-535": "AP-535",
        "AP-565": "AP-565",
        "AP-567": "AP-567",
        "AP-584": "AP-584",
        "Ap-587": "AP-587",
    }.items()
}


class Command(ArubaImportCommand):
    help = "Import explicitly documented Aruba AP enterprise-mesh support gaps."
    products = PRODUCTS
    document_version = "Official Aruba Central 2.5.7 mesh documentation; accessed 2026-10-22"
