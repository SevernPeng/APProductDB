from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "SE3005": {
        "url": "https://support.linksys.com/kb/article/4998-en/",
        "page": "SE3005 support page, current English version, version 2 specifications",
        "title": "Linksys SE3005 official support and specifications",
        "values": {
            "ethernet_interfaces": t("5 x 10/100/1000 Mbps auto-sensing Ethernet ports"),
            "management_type": t("Unmanaged, plug-and-play"),
            "qos_support": t("IEEE 802.1p QoS"),
            "installation": t("Desktop"),
            "dimensions_mm": t("120 x 88 x 26 mm", "SE3005 version 2"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Linksys SE3005 version 2 specifications."
    products = PRODUCTS
    document_version = "Current Linksys official support page, version 2 specifications; accessed 2026-10-16"
    brand_name = "Linksys"
