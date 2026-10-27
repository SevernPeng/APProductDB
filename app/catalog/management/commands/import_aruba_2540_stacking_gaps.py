from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    n,
    t,
)


URL = (
    "https://arubanetworking.hpe.com/techdocs/central/2.5.8/content/nms/"
    "aos-switch/supported-platforms/supported_switches.htm"
)

NO_STACKING = {
    "stacking": t("Not supported (standalone switch only)", "Official AOS-S platform table lists 2540 switch stacking support as N/A"),
    "stacking_units": n(1, "No multi-switch stack; one standalone unit"),
    "stacking_bandwidth_gbps": n(0, "No VSF/BPS stacking fabric; stacking bandwidth is 0 Gbps"),
}

PRODUCTS = {
    model: {
        "url": URL,
        "page": "Supported AOS-S Switch Series, Software Versions, and Switch Stacking table",
        "title": "HPE Aruba Networking Central Supported AOS-S Platforms",
        "values": dict(NO_STACKING),
    }
    for model in (
        "2540 24G 4SFP+ Switch",
        "2540 24G PoE+ 4SFP+ Switch",
        "2540 48G 4SFP+ Switch",
        "2540 48G PoE+ 4SFP+ Switch",
    )
}


class Command(ArubaImportCommand):
    help = "Import officially documented no-stacking status for Aruba 2540 switches."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking Central documentation; accessed 2026-10-22"
