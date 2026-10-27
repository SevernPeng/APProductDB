from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://www.downloads.netgear.com/files/GDC/datasheet/en/JGS516v2-JGS524v2.pdf"


def item(model, ports, capacity, power):
    return {
        "url": URL,
        "page": "pp. 1-3, JGS516v2/JGS524v2 specification table",
        "title": "NETGEAR JGS516v2/JGS524v2 Data Sheet (3 February 2022)",
        "values": {
            "ethernet_interfaces": t(f"{ports} x 10/100/1000BASE-T RJ45"),
            "management_type": t("Unmanaged, instant plug-and-play"),
            "switching_capacity_gbps": n(capacity),
            "mac_address_table": t("8K entries"),
            "packet_buffer_mb": n("0.250", "RAM buffer: 256 KB"),
            "jumbo_frame_bytes": n(9216, "Jumbo Frame Support: up to 9 KB"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p and TOS prioritization"),
            "installation": t("Desktop or standard 19-inch rack mount"),
            "max_power_consumption_w": n(power),
            "dimensions_mm": t("328 x 169 x 43 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    }


PRODUCTS = {
    "JGS516": item("JGS516", 16, 32, "11.8"),
    "JGS524": item("JGS524", 24, 48, "17.9"),
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR JGS516v2 and JGS524v2 specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR JGS516v2/JGS524v2 datasheet, 3 February 2022; accessed 2026-10-20"
    brand_name = "NETGEAR"
