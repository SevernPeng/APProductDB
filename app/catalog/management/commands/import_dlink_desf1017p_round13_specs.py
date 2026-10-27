from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    t,
)


DS = "https://www.dlink.com.vn/Downloads/DES-F1017P/datasheet/DES-F1017P-E%20DS.pdf"


PRODUCTS = {
    "DES-F1017P-E": {
        "url": DS,
        "page": "pp. 1-3, product highlights, function and physical specifications",
        "title": "D-Link DES-F1017P-E 250M 16-Port Fast Ethernet PoE Switch Datasheet",
        "values": {
            "dimensions_mm": t("285 x 180 x 44 mm", "Dimensions: 285 x 180 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C", "Operating temperature: 0 to 40 °C (32 to 104 °F)"),
            "installation": t("Desktop with mounting kit", "Size: Desktop (with Mounting Kit)"),
            "flow_control": t("IEEE 802.3x flow control", "Standards: IEEE 802.3x flow control"),
            "transmission_method": t("Store-and-forward", "Transmission method: Store-and-forward"),
            "vlan_support": t("Port isolation VLAN mode", "VLAN mode isolates downlink ports to suppress network storms and improve performance"),
            "qos_support": t("Video QoS mode", "QoS mode increases priority for video traffic"),
            "extend_mode": b(True, "Extend mode supports data and PoE up to 250 m on ports 1-8 at 10 Mbps"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified D-Link DES-F1017P-E physical and selectable smart-mode specifications."
    products = PRODUCTS
    document_version = "Updated 2019-05-19; accessed 2026-10-22"
    brand_name = "D-Link"
