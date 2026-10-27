from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


DOC = "https://documentation.grandstream.com/knowledge-base"


def common(temperature):
    return {
        "operating_temperature_c": t(temperature),
        "fast_roaming": t("802.11k/v/r"),
    }


PRODUCTS = {
    "GWN7662": {
        "url": f"{DOC}/gwn7662-technical-specifications/",
        "page": "GWN7662 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7662 official technical specifications",
        "values": {
            **common("-10 to 45 °C"),
            "antenna_gain_dbi": t("2.4 GHz: 3.65 dBi; 5 GHz: 5.26 dBi"),
        },
    },
    "GWN7664": {
        "url": f"{DOC}/gwn7664-technical-specifications/",
        "page": "GWN7664 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7664 official technical specifications",
        "values": common("0 to 50 °C"),
    },
    "GWN7664E": {
        "url": f"{DOC}/gwn7664e-technical-specifications/",
        "page": "GWN7664E Technical Specifications, updated 2026",
        "title": "Grandstream GWN7664E official technical specifications",
        "values": common("0 to 50 °C"),
    },
    "GWN7664LR": {
        "url": f"{DOC}/gwn7664lr-technical-specifications/",
        "page": "GWN7664LR Technical Specifications, updated 2026",
        "title": "Grandstream GWN7664LR official technical specifications",
        "values": common("-30 to 60 °C"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7662/7664/7664E/7664LR specifications."
    products = PRODUCTS
    document_version = "Grandstream official technical documentation updated 2026; accessed 2026-10-16"
    brand_name = "Grandstream"
