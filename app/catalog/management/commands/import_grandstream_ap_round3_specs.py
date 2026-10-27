from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DOC = "https://documentation.grandstream.com/knowledge-base"


PRODUCTS = {
    "GWN7660E": {
        "url": f"{DOC}/gwn7660e-technical-specifications/",
        "page": "GWN7660E Technical Specifications, updated 2026",
        "title": "Grandstream GWN7660E official technical specifications",
        "values": {
            "rate_2g_mbps": n(573.5),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7660ELR": {
        "url": f"{DOC}/gwn7660elr-technical-specifications/",
        "page": "GWN7660ELR Technical Specifications, updated 2026",
        "title": "Grandstream GWN7660ELR official technical specifications",
        "values": {
            "operating_temperature_c": t("-30 to 60 °C"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7661": {
        "url": f"{DOC}/gwn7661-technical-specifications/",
        "page": "GWN7661 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7661 official technical specifications",
        "values": {
            "rate_2g_mbps": n(573.5),
            "rate_5g_mbps": n(1201),
            "mimo_2g": t("2x2:2 MIMO"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "dimensions_mm": t("135 x 86 x 38.5 mm"),
            "poe_output": t("Two Gigabit Ethernet PSE ports, maximum 6 W output per port"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
    "GWN7661E": {
        "url": f"{DOC}/gwn7661e-technical-specifications/",
        "page": "GWN7661E Technical Specifications, updated 2026",
        "title": "Grandstream GWN7661E official technical specifications",
        "values": {
            "rate_2g_mbps": n(573.5),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2:2 MIMO"),
            "operating_temperature_c": t("0 to 45 °C"),
            "dimensions_mm": t("135 x 86 x 38.5 mm"),
            "poe_output": t("Two Gigabit Ethernet PSE ports, maximum 6 W output per port"),
            "fast_roaming": t("802.11k/v/r"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7660E/ELR and GWN7661/E specifications."
    products = PRODUCTS
    document_version = "Grandstream official technical documentation updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
