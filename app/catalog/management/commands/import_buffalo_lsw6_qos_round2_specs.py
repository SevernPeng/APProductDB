from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "LSW6-GT-5ESL": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-5esl_nbk.html",
        "page": "Specifications / supported functions",
        "title": "Buffalo LSW6-GT-5ESL/NBK Product Page",
        "values": {
            "qos_support": t(
                "Not supported",
                "The official exhaustive supported-function list omits IEEE 802.1p/QoS; the model is an unmanaged plug-and-play switch",
            ),
        },
    },
    "LSW6-GT-8ESL": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-8esl_nbk.html",
        "page": "Specifications / supported functions",
        "title": "Buffalo LSW6-GT-8ESL/NBK Product Page",
        "values": {
            "qos_support": t(
                "Not supported",
                "The official exhaustive supported-function list omits IEEE 802.1p/QoS; the model is an unmanaged plug-and-play switch",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Complete Buffalo LSW6-GT-ESL QoS support from official feature inventories."
    products = PRODUCTS
    document_version = "Official Buffalo Japan product pages; accessed 2026-10-27"
    brand_name = "Buffalo"
