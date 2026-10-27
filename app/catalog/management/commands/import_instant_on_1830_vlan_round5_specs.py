from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = "https://www.arubanetworks.com/techdocs/InstantOn_1830_Switch/InstantOn_1830_MCG.pdf"


PRODUCTS = {
    model: {
        "url": URL,
        "page": "VLAN > VLAN Configuration",
        "title": "Aruba Instant On 1830 Switch Series Management and Configuration Guide",
        "values": {
            "vlan_count": n(
                64,
                "Instant On 1830 Switch Series switches support up to 64 VLANs",
            ),
        },
    }
    for model in ("JL810A", "JL811A", "JL812A", "JL813A", "JL814A", "JL815A")
}


class Command(VerifiedImportCommand):
    help = "Import the official VLAN capacity for Instant On 1830 switches."
    products = PRODUCTS
    document_version = "Official Instant On 1830 management guide; accessed 2026-10-27"
    brand_name = "Instant On"
