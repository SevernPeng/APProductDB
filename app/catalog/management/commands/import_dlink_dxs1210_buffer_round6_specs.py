from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


HIG = "https://support.dlink.com/resource/PRODUCTS/DXS-1210-28S/REVA/DXS-1210-28T_S_REVA_HARDWARE_INSTALL_GUIDE_v1.00_WW.pdf"


PRODUCTS = {
    model: {
        "url": HIG,
        "page": "Appendix A, Performance Specification table",
        "title": "D-Link DXS-1210 Series Hardware Installation Guide v1.00 (WW)",
        "values": {
            "packet_buffer_mb": n(4, f"Packet buffer: {model} - 4 MB"),
        },
    }
    for model in ("DXS-1210-28T", "DXS-1210-28S")
}


class Command(VerifiedImportCommand):
    help = "Import D-Link DXS-1210-28T/28S packet-buffer specifications from the official hardware guide."
    products = PRODUCTS
    document_version = "Hardware Installation Guide v1.00 (WW); accessed 2026-10-22"
    brand_name = "D-Link"

