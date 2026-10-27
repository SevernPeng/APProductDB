from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


INSIGHT_URL = "https://kb.netgear.com/000044346/How-do-I-set-up-an-Insight-Managed-Wireless-Access-Point-in-the-Insight-app-or-Cloud-Portal"


PRODUCTS = {
    "WAC730": {
        "url": "https://www.downloads.netgear.com/files/GDC/BCWM/BCWM2_UM_EN.pdf",
        "page": "p. 63, Enable Fast Roaming for a WiFi Network",
        "title": "NETGEAR Business Central Wireless Manager 2.1 User Manual",
        "values": {"fast_roaming": t("IEEE 802.11r fast roaming under Business Central Wireless Manager")},
    },
    **{
        model: {
            "url": INSIGHT_URL,
            "page": "Fast Roaming setup and applicable-products list",
            "title": "NETGEAR Insight Managed Wireless Access Point Setup Support Article",
            "values": {"fast_roaming": t("NETGEAR Insight Fast Roaming")},
        }
        for model in ("WAX610", "WAX615", "WAX620", "WAX625", "WBE708")
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR Insight and Business Central fast-roaming support."
    products = PRODUCTS
    document_version = "Official NETGEAR support article and management manual; accessed 2026-10-20"
    brand_name = "NETGEAR"
