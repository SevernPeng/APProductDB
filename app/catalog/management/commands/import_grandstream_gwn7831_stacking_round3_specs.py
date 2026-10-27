from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://documentation.grandstream.com/knowledge-base/gwn78xx-stacking-feature-guide/"


PRODUCTS = {
    "GWN7831": {
        "url": URL,
        "title": "Grandstream GWN78xx Stacking Feature Guide",
        "page": "Maximum Supported Devices; Port & Speed Requirements; Supported Devices (updated April 30, 2026)",
        "values": {
            "stacking": t(
                "Hardware stacking supported on current firmware; same-model switches only",
                "GWN7831 supports hardware stacking beginning with firmware 1.0.15.126; all members must be the same model and firmware version",
            ),
            "stacking_units": n(8, "GWN7831: up to 8 devices in a stack"),
            "stacking_ports": t(
                "SFP+ ports 25-28; stacking links operate at 10 Gbps",
                "GWN7831 physical stack ports: SFP+ 25-28; connection rate must be set to 10Gbps on all stacking ports",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Update GWN7831 stacking specifications from the current official feature guide."
    products = PRODUCTS
    document_version = "Updated 2026-04-30; accessed 2026-10-21"
    brand_name = "Grandstream"
