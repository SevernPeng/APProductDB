from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


SOURCE = "https://www.engeniustech.com/wp-content/uploads/2024/01/FIT-Series-Access-Points.pdf"

PRODUCTS = {
    model: {
        "url": SOURCE,
        "page": "Software Lists / Optimize Performance",
        "title": "EnGenius Fit Series Access Points official feature matrix",
        "values": {
            "fast_roaming": t("802.11k/v/r", "Fit Series supports 802.11k, 802.11v and 802.11r fast roaming"),
        },
    }
    for model in ("EWS276-FIT", "EWS356-FIT", "EWS357-FIT", "EWS850-FIT")
}


class Command(VerifiedImportCommand):
    help = "Import official EnGenius Fit-series fast-roaming support."
    products = PRODUCTS
    document_version = "EnGenius Fit Series Access Points official PDF; accessed 2026-10-16"
    brand_name = "EnGenius"
