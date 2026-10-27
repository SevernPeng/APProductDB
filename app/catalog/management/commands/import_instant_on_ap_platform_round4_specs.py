from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


ROAMING_URL = "https://community.instant-on.hpe.com/blogs/jamie-easly1/2020/10/23/instant-on-wireless-release-notes"


def roaming_product(model):
    values = {
        "fast_roaming": t(
            "802.11k assisted roaming with seamless handoff between Instant On access points",
            "Instant On AP software supports 802.11k for a better roaming experience; current AP datasheets describe seamless handoff between APs",
        ),
    }
    return {
        "url": ROAMING_URL,
        "title": "HPE Networking Instant On AP Software Release Notes",
        "page": "Version 2.3.0 - support of 802.11k for better roaming experience",
        "values": values,
    }


PRODUCTS = {
    model: roaming_product(model)
    for model in ("AP21", "AP22", "AP22D", "AP25", "AP27")
}

class Command(VerifiedImportCommand):
    help = "Import official Instant On AP platform roaming and wireless-network limits."
    products = PRODUCTS
    document_version = "Official AP software release notes; accessed 2026-10-21"
    brand_name = "Instant On"
