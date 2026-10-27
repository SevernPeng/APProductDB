from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "eKit AP266": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/e54ac3a76f614189835e8e99aa514939/M3T1A590N1051921978522906890/Huawei%20eKitEngine%20AP266%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "IEEE standards table",
        "title": "Huawei eKitEngine AP266 Wireless Access Point Datasheet",
        "values": {
            "fast_roaming": t("IEEE 802.11k/v/r"),
        },
    },
    "eKit AP271H-P": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/bdbf47a5aca54cae8d2e44d69b51b23a/M3T1A590N1263931343900192999/HUAWEI%20eKitEngine%20AP271H-P%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "WLAN features table",
        "title": "Huawei eKitEngine AP271H-P Wireless Access Point Datasheet",
        "values": {
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei eKit AP266 and AP271H-P roaming specifications."
    products = PRODUCTS
    document_version = "Current official Huawei eKit datasheets; accessed 2026-10-20"
    brand_name = "Huawei"
