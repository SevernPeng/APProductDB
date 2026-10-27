from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


CATALOG_2021 = "https://www.dahuasecurity.com/asset/upload/uploads/soft/20211207/Catalog_Dahua-Network-Transmission-Products-and-Solutions_V2.0_EN_202111%2836P%29.pdf"
CATALOG_PFWB = "https://www.dahuasecurity.com/asset/upload/uploads/soft/20210930/Dahua_Technology_Network_Transmission_catalog_2021_H26.pdf"


PRODUCTS = {
    "DH-PFM886-15": {
        "url": CATALOG_2021,
        "page": "p. 24, Outdoor Wireless Transmission Device comparison",
        "title": "Dahua Network Transmission Products and Solutions Catalog",
        "values": {
            "lightning_protection_kv": t(
                "Common mode 4 kV; differential mode 1.5 kV",
                "Lightning Protection: Common Mode 4KV, Differential Mode 1.5KV",
            ),
        },
    },
    "PFM886-15": {
        "url": CATALOG_2021,
        "page": "p. 24, Outdoor Wireless Transmission Device comparison",
        "title": "Dahua Network Transmission Products and Solutions Catalog",
        "values": {
            "lightning_protection_kv": t(
                "Common mode 4 kV; differential mode 1.5 kV",
                "Lightning Protection: Common Mode 4KV, Differential Mode 1.5KV",
            ),
        },
    },
    "DH-PFWB5-90ac": {
        "url": CATALOG_PFWB,
        "page": "p. 19, V-Radio Wireless Bridge Series comparison",
        "title": "Dahua Network Transmission Catalog 2021",
        "values": {
            "lightning_protection_kv": t(
                "Common mode 3 kV; differential mode 1 kV",
                "Lightning Protection: Common Mode 3KV, Differential Mode 1KV",
            ),
        },
    },
    "PFWB5-90ac": {
        "url": CATALOG_PFWB,
        "page": "p. 19, V-Radio Wireless Bridge Series comparison",
        "title": "Dahua Network Transmission Catalog 2021",
        "values": {
            "lightning_protection_kv": t(
                "Common mode 3 kV; differential mode 1 kV",
                "Lightning Protection: Common Mode 3KV, Differential Mode 1KV",
            ),
        },
    },
    "PFM885-I": {
        "url": CATALOG_2021,
        "page": "p. 25, Indoor Wireless Transmission Device comparison",
        "title": "Dahua Network Transmission Products and Solutions Catalog",
        "values": {
            "lightning_protection_kv": t(
                "Not supported", "Lightning Protection: --"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified Dahua wireless-bridge lightning-protection specifications."
    products = PRODUCTS
    document_version = "2021 comparison catalogs; accessed 2026-10-22"
    brand_name = "Dahua"
