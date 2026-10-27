from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "GWN7670WM": {
        "url": "https://www.grandstream.com/hubfs/Partner%20Portal/Comparison%20Charts/Grandstream/GWN_Indoor%20Comparison%20Chart.pdf",
        "page": "GWN7670WM PoE/PoE+ row",
        "title": "Grandstream GWN Series Master Comparison Chart - Indoor",
        "values": {
            "poe_output": t(
                "LAN2/LAN3 PSE output, 12 W total",
                "PSE max output: total 12 W power consumption for LAN2/LAN3",
            ),
        },
    },
    "GWN7672WM": {
        "url": "https://documentation.grandstream.com/knowledge-base/gwn7672wm-technical-specifications/",
        "page": "Interfaces and Power table",
        "title": "Grandstream GWN7672WM Technical Specifications",
        "values": {
            "poe_output": t(
                "Not supported; the single 5GbE RJ45 port is PoE input only",
                "Network Interface: 1 x 5 GbE RJ45 port with PoE input; no power-output interface is listed",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified PoE-output specifications for Grandstream wall-mount access points."
    products = PRODUCTS
    document_version = "Current official comparison chart and technical specifications; accessed 2026-10-22"
    brand_name = "Grandstream"
