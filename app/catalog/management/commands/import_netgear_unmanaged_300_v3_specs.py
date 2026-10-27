from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL = "https://www.downloads.netgear.com/files/GDC/GS316v3/GS316v3_DS.pdf"


def item(model, ports, capacity, buffer_mb, mac, power, dimensions, installation):
    return {
        "url": URL,
        "page": "pp. 1, 3-4, model comparison table",
        "title": "NETGEAR Gigabit Unmanaged Essentials Switch Data Sheet (26 March 2025)",
        "values": {
            "ethernet_interfaces": t(f"{ports} x 10/100/1000BASE-T RJ45"),
            "management_type": t("Unmanaged, plug-and-play; no setup required"),
            "switching_capacity_gbps": n(capacity, f"Non-blocking bandwidth: {capacity} Gbps"),
            "mac_address_table": t(f"{mac} entries"),
            "packet_buffer_mb": n(buffer_mb),
            "jumbo_frame_bytes": n(9216),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p priority QoS and DSCP; weighted round robin queues"),
            "fanless": b(True, "Fan/Fanless: Fanless"),
            "installation": t(installation),
            "max_power_consumption_w": n(power),
            "dimensions_mm": t(dimensions),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    }


PRODUCTS = {
    "GS305": item("GS305", 5, 10, "0.125", "2K", "2.15", "101 x 94 x 29 mm (W x D x H)", "Desktop or wall mount"),
    "GS308": item("GS308", 8, 16, "0.188", "8K", "3.04", "158 x 101 x 29 mm (W x D x H)", "Desktop or wall mount"),
    "GS316": item("GS316", 16, 32, "4.1", "8K", "8.10", "286 x 102 x 27 mm (W x D x H)", "Desktop or wall mount"),
    "GS324": item("GS324", 24, 48, "4.1", "8K", 12, "252 x 180 x 44 mm (W x D x H)", "Desktop or rack mount"),
    "GS348": item("GS348", 48, 96, "1.5", "8K", 23, "440 x 202 x 43 mm (W x D x H)", "Desktop or rack mount"),
}


class Command(VerifiedImportCommand):
    help = "Import manually verified current NETGEAR GS300 unmanaged switch specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR GS300 unmanaged datasheet, 26 March 2025; accessed 2026-10-20"
    brand_name = "NETGEAR"
