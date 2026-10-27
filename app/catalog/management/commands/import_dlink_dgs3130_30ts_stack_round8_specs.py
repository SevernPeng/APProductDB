from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


FAQ = "https://meweb.dlink.com/in/en/support/faq/switches/layer-3-gigabit/dgs-3130-stacking-bandwidth"


PRODUCTS = {
    "DGS-3130-30TS": {
        "url": FAQ,
        "page": "DGS-3130 Stacking Bandwidth FAQ, 2-port and 4-port configurations",
        "title": "D-Link DGS-3130 Stacking Bandwidth Support FAQ",
        "values": {
            "stacking_bandwidth_gbps": n(
                80,
                "Up to 80 Gbps full-duplex using a four-port SFP+ or hybrid stacking configuration",
            ),
            "stacking_ports": t(
                "Up to 4 front-panel stacking ports: ports 25-26 and 29-30 for hybrid mode, or ports 27-30 for four-port SFP+ mode",
                "Four-port hybrid: ports 25, 26, 29 and 30; four-port SFP+: ports 27, 28, 29 and 30",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import D-Link DGS-3130-30TS stacking bandwidth and port details from the official support FAQ."
    products = PRODUCTS
    document_version = "Current official support FAQ; accessed 2026-10-22"
    brand_name = "D-Link"

