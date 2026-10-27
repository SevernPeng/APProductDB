from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
)


URL = "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9200/software/release/17-15/configuration_guide/rtng/b_1715_rtng_9200_cg/protocol_independent_features.html"


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Policy-Based Routing chapter, Catalyst 9200 Series support and restrictions",
        "title": "Cisco IOS XE 17.15 Catalyst 9200 Series Routing Configuration Guide",
        "values": {
            "pbr_support": b(
                True,
                "IPv4 policy-based routing with route maps and ACL traffic classification; supported on Catalyst 9200 Series from IOS XE Fuji 16.9.2",
            ),
        },
    }
    for model in (
        "C9200L-24T-4X",
        "C9200L-24P-4X",
        "C9200L-48T-4X",
        "C9200L-48P-4X",
    )
}


class Command(VerifiedImportCommand):
    help = "Import officially documented PBR support for Cisco Catalyst 9200L switches."
    products = PRODUCTS
    document_version = "Cisco IOS XE 17.15 routing guide; accessed 2026-10-22"
    brand_name = "Cisco"
