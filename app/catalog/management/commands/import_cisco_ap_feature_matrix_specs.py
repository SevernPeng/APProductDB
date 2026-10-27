from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_MATRIX = "https://www.cisco.com/c/en/us/td/docs/wireless/access_point/feature-matrix/ap-feature-matrix.html"
URL_POWER = "https://www.cisco.com/c/en/us/support/docs/wireless/catalyst-9100-access-points/215467-cisco-access-point-power-requirements-qu.html"


FAST_ROAM = t(
    "802.11r Fast Transition, Adaptive 11r, OKC and CCKM fast roaming; exact availability depends on controller and authentication mode"
)


def matrix_values(mesh):
    return {
        "fast_roaming": FAST_ROAM,
        "mesh_support": b(mesh, "Cisco IOS XE AP feature matrix Mesh Mode support"),
    }


PRODUCTS = {
    "C9105AXI": {
        "url": URL_MATRIX,
        "page": "Wi-Fi 6/6E FlexConnect and Infrastructure feature matrices, updated 2026-09-10",
        "title": "Cisco Wireless Access Point Feature Matrix",
        "values": matrix_values(False),
    },
    "C9115AXI": {
        "url": URL_POWER,
        "page": "Table 3 maximum power draw; feature support cross-checked in the current AP feature matrix",
        "title": "Cisco Aironet and Catalyst AP Power Requirements Reference (updated 2026-10-12)",
        "values": {
            **matrix_values(False),
            "max_power_consumption_w": n(21.4, "Maximum power draw for Cisco 9115"),
        },
    },
    "C9120AXI": {
        "url": URL_MATRIX,
        "page": "Wi-Fi 6/6E FlexConnect and Infrastructure feature matrices, updated 2026-09-10",
        "title": "Cisco Wireless Access Point Feature Matrix",
        "values": matrix_values(False),
    },
    "C9124AXE": {
        "url": URL_MATRIX,
        "page": "Wi-Fi 6/6E Infrastructure feature matrix and release note 4, updated 2026-09-10",
        "title": "Cisco Wireless Access Point Feature Matrix",
        "values": matrix_values(True),
    },
    "CW9105AXW": {
        "url": URL_MATRIX,
        "page": "Wi-Fi 6/6E FlexConnect and Infrastructure feature matrices, updated 2026-09-10",
        "title": "Cisco Wireless Access Point Feature Matrix",
        "values": matrix_values(False),
    },
    **{
        model: {
            "url": URL_MATRIX,
            "page": "Wi-Fi 7 FlexConnect feature matrix, updated 2026-09-10",
            "title": "Cisco Wireless Access Point Feature Matrix",
            "values": {"fast_roaming": FAST_ROAM},
        }
        for model in (
            "CW9171I",
            "CW9172I",
            "CW9172H",
            "CW9174I",
            "CW9176I",
            "CW9178I",
        )
    },
}


class Command(VerifiedImportCommand):
    help = "Import current Cisco AP fast-roaming, mesh and corrected power specifications."
    products = PRODUCTS
    document_version = "Cisco AP feature matrix 2026-09-10 and current support references; accessed 2026-10-16"
    brand_name = "Cisco"
