from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
)
from catalog.management.commands.import_aruba_switch_1920s_specs import PRODUCTS as HPE_PRODUCTS


PRODUCTS = {
    "HPE 1920S 8G PPoE+ 65W Switch": {
        **HPE_PRODUCTS["1920S 8G PPoE+ 65W Switch"],
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified HPE OfficeConnect 1920S specifications for the legacy Other-brand record."
    products = PRODUCTS
    document_version = "Official retired HPE QuickSpecs version 4; accessed 2026-10-21"
    brand_name = "Other"
