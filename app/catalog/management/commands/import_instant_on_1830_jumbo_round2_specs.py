from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL = "https://arubanetworking.hpe.com/techdocs/InstantOn_1830_Switch/InstantOn_1830_MCG.pdf"


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Management and Configuration Guide, Global Configuration / Jumbo Frames",
        "title": "HPE Networking Instant On 1830 Switch Series Management and Configuration Guide",
        "values": {
            "jumbo_frame_bytes": n(
                9216,
                "When Jumbo Frames is enabled, frame size is limited to 9216 bytes",
            ),
        },
    }
    for model in ("JL810A", "JL811A", "JL812A", "JL813A", "JL814A", "JL815A")
}


class Command(VerifiedImportCommand):
    help = "Import the firmware-supported jumbo-frame limit for Instant On 1830 switches."
    products = PRODUCTS
    document_version = "Current official Instant On 1830 management guide; accessed 2026-10-21"
    brand_name = "Instant On"
