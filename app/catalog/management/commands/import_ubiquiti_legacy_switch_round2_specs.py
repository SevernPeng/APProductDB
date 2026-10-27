from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


TECH_SPECS = "https://techspecs.ui.com/unifi/switching/{}"


PRODUCTS = {
    "US-8-60W": {
        "url": TECH_SPECS.format("us-8-60w"),
        "page": "Overview, Performance, and Hardware",
        "title": "Ubiquiti UniFi 8 PoE (Gen1) Tech Specs",
        "values": {
            "poe_budget_w": n(48, "Total PoE Availability: 48W"),
            "vlan_count": n(256, "Supported VLANs: 256"),
            "mac_address_table": t("16,000 entries", "MAC Address Table Size: 16,000"),
            "packet_buffer_mb": n(1.5, "Packet Buffer Size: 1.5 MB"),
        },
    },
    "US-8-150W": {
        "url": TECH_SPECS.format("us-8-150w"),
        "page": "Overview and Performance",
        "title": "Ubiquiti UniFi 8 PoE, SFP (Gen1) Tech Specs",
        "values": {
            "poe_budget_w": n(130, "Total PoE Availability: 130W"),
            "vlan_count": n(256, "Supported VLANs: 256"),
            "mac_address_table": t("16,000 entries", "MAC Address Table Size: 16,000"),
            "packet_buffer_mb": n(1.5, "Packet Buffer Size: 1.5 MB"),
        },
    },
    "US-24-500W": {
        "url": TECH_SPECS.format("us-24-500w"),
        "page": "Overview",
        "title": "Ubiquiti UniFi Standard 24 PoE Hi-Power (Gen1) Tech Specs",
        "values": {
            "poe_budget_w": n(500, "Total PoE Availability: 500W"),
        },
    },
    "US-48-500W": {
        "url": TECH_SPECS.format("us-48-500w"),
        "page": "Overview",
        "title": "Ubiquiti UniFi Standard 48 PoE (Gen1) Tech Specs",
        "values": {
            "poe_budget_w": n(500, "Total PoE Availability: 500W"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current official Ubiquiti legacy-switch PoE and capacity specifications."
    products = PRODUCTS
    document_version = "Current official Ubiquiti Tech Specs; accessed 2026-10-23"
    brand_name = "Ubiquiti"
