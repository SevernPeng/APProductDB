from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


WBE708_DS = "https://www.downloads.netgear.com/files/GDC/WBE708/WBE708_DS.pdf"
AXM765V2_IG = "https://www.downloads.netgear.com/files/GDC/AXM765/AXM765v2_IG_EN.pdf"


PRODUCTS = {
    "WBE708": {
        "url": WBE708_DS,
        "page": "pp. 5-7, technical and radio/antenna specifications",
        "title": "NETGEAR WBE708 WiFi 7 Access Point Data Sheet",
        "values": {
            "rate_5g_mbps": n(4332, "5 GHz: 2x2 (4332 Mbps)"),
            "max_channel_width_mhz": n(240, "5 GHz: 20/40/80/160/240 MHz"),
            "antenna_type": t(
                "Four internal cable-fed PIFA antennas (2 x 2.4 GHz, 2 x 5 GHz), optimized for omnidirectional coverage",
                "Four internal PIFA antennas; two dedicated to 2.4 GHz and two to 5 GHz; placement optimized for omnidirectional coverage",
            ),
            "antenna_gain_dbi": t(
                "2.4 GHz: 3.3 dBi; 5 GHz: 3.8 dBi",
                "Antenna gain: 2.4 GHz 3.3 dBi; 5 GHz 3.8 dBi",
            ),
        },
    },
    "AXM765": {
        "url": AXM765V2_IG,
        "page": "p. 1, Technical Specifications",
        "title": "NETGEAR AXM765v2 10GBASE-T SFP+ Module Installation Guide",
        "values": {
            "dimensions_mm": t(
                "13.8 x 13.7 x 68.8 mm (H x W x D)",
                "Dimensions (H x W x D): 13.8 mm x 13.7 mm x 68.8 mm",
            ),
            "operating_temperature_c": t("0 to 40 °C", "Operating temperature: 0–40 °C"),
            "max_power_consumption_w": n(2.5, "Power consumption: 2.5 W"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current NETGEAR WBE708 corrections and AXM765v2 physical specifications."
    products = PRODUCTS
    document_version = (
        "WBE708 data sheet NG_DS_AV_WBE708-061726 (2026-06-17) and "
        "AXM765v2 installation guide (2022-03); accessed 2026-10-21"
    )
    brand_name = "NETGEAR"
