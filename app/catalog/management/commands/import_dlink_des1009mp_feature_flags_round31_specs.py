from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    t,
)


SOURCE_URL = "https://dlink.ru/up/support/_files/D-Link_Business_Switches.pdf"


PRODUCTS = {
    "DES-1009MP": {
        "url": SOURCE_URL,
        "page": "Fast Ethernet unmanaged switches comparison, DES-1009MP column",
        "title": "D-Link Business Switches Product Guide",
        "values": {
            "extend_mode": b(False, "Operating modes/Extend: not supported for DES-1009MP"),
            "poe_auto_recovery": b(False, "PoE auto-recovery: not supported for DES-1009MP"),
            "qos_support": t("Not supported", "IEEE 802.1p QoS: not supported for DES-1009MP"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Complete unsupported DES-1009MP feature flags from D-Link's comparison table."
    products = PRODUCTS
    document_version = "Current official D-Link business switches guide; accessed 2026-10-27"
    brand_name = "D-Link"
