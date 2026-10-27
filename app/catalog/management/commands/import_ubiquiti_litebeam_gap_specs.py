from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


URL = "https://dl.ui.com/datasheets/LiteBeam/LiteBeam_AC_Gen2_DS.pdf"


def item():
    return {
        "url": URL,
        "page": "p. 4, LBE-5AC-Gen2 specifications",
        "title": "Ubiquiti LiteBeam AC Gen2 Data Sheet",
        "values": {
            "lightning_protection_kv": t(
                "±24 kV contact / air",
                "ESD/EMP protection: ±24 kV contact / air",
            ),
        },
    }


PRODUCTS = {
    "LBE-5AC-GEN2": item(),
    "airMAX LBE-5AC-GEN2": item(),
}


class Command(VerifiedImportCommand):
    help = "Import exact Ubiquiti LiteBeam LBE-5AC-Gen2 ESD/EMP protection."
    products = PRODUCTS
    document_version = "Official LiteBeam AC Gen2 data sheet 7JLAJ102819; accessed 2026-10-23"
    brand_name = "Ubiquiti"
