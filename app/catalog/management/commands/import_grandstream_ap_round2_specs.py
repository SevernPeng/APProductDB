from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DOC = "https://documentation.grandstream.com/knowledge-base"


PRODUCTS = {
    "GWN7615": {
        "url": f"{DOC}/gwn7615-technical-specifications/",
        "page": "GWN7615 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7615 official technical specifications",
        "values": {
            "rate_2g_mbps": n(450),
            "rate_5g_mbps": n(1300),
            "mimo_2g": t("3x3:3 MIMO"),
            "ethernet_interfaces": t("2 x Gigabit Ethernet ports"),
            "operating_temperature_c": t("0 to 40 °C"),
            "max_power_consumption_w": n(12.5),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
    "GWN7625": {
        "url": f"{DOC}/gwn7625-technical-specifications/",
        "page": "GWN7625 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7625 official technical specifications",
        "values": {
            "operating_temperature_c": t("0 to 40 °C"),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
    "GWN7660": {
        "url": f"{DOC}/gwn7660-technical-specifications/",
        "page": "GWN7660 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7660 official technical specifications",
        "values": {
            "rate_2g_mbps": n(573.5),
            "rate_5g_mbps": n(1201),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "operating_temperature_c": t("0 to 45 °C"),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
    "GWN7660LR": {
        "url": f"{DOC}/gwn7660lr-technical-specifications/",
        "page": "GWN7660LR Technical Specifications, updated 2026",
        "title": "Grandstream GWN7660LR official technical specifications",
        "values": {
            "operating_temperature_c": t("-30 to 60 °C"),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7615/7625/7660/7660LR specifications."
    products = PRODUCTS
    document_version = "Grandstream official technical documentation updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
