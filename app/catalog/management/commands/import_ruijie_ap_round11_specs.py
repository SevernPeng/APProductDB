from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
)
from catalog.management.commands.import_ruijie_ap_round3_specs import cd_values


SOURCE_URL = "https://www.ruijie.com.cn/cp/wx-swap/ap680cd/"


PRODUCTS = {
    "RG-AP680": {
        "url": SOURCE_URL,
        "page": (
            "Current RG-AP680(CD) hardware/software specifications; "
            "the database base model omits the (CD) suffix"
        ),
        "title": "Ruijie RG-AP680(CD) official product specifications",
        "values": cd_values(),
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified current RG-AP680(CD) specifications for the database RG-AP680 base-model alias."
    products = PRODUCTS
    document_version = "Current official Ruijie product page; accessed 2026-10-22"
    brand_name = "Ruijie"
