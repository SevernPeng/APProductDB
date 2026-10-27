from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


URL = "https://kb.netgear.com/000070708/PR60X-Firmware-Version-3-0-0-105"


PRODUCTS = {
    "PR60X": {
        "url": URL,
        "page": "New Features and Enhancements, SD-WAN — Software-Defined WAN",
        "title": "NETGEAR PR60X Firmware Version 3.0.0.105 Release Notes",
        "values": {
            "sd_wan": t(
                "SASE-enabled SD-WAN with encrypted site-to-site mesh tunnels and policy-driven multi-WAN traffic steering",
                "SD-WAN establishes encrypted site-to-site secured mesh tunnels between multiple PR60X routers and supports policy-driven traffic steering across WAN links",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the current firmware-confirmed NETGEAR PR60X SD-WAN capability."
    products = PRODUCTS
    document_version = "PR60X firmware 3.0.0.105 release notes, 2026-05-01; accessed 2026-10-21"
    brand_name = "NETGEAR"
