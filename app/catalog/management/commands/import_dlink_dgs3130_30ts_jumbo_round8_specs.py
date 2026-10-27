from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


HIG = "https://support.dlink.com/resource/products/DGS-3130-SERIES/REVB/DGS-3130%20Series_B1_HW%20Installation%20Guide_v1.10.pdf"


PRODUCTS = {
    "DGS-3130-30TS": {
        "url": HIG,
        "page": "Appendix A, Performance table",
        "title": "D-Link DGS-3130 Series Revision B1 Hardware Installation Guide v1.10",
        "values": {"jumbo_frame_bytes": n(9216, "Jumbo Frame Size: 9K Bytes (9216 Bytes)")},
    },
}


class Command(VerifiedImportCommand):
    help = "Import the D-Link DGS-3130-30TS 9K jumbo-frame size from the Revision B1 hardware guide."
    products = PRODUCTS
    document_version = "Revision B1 Hardware Installation Guide v1.10; accessed 2026-10-22"
    brand_name = "D-Link"

