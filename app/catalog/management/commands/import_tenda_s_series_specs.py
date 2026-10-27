from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


def specs(ports, dimensions, capacity, forwarding, buffer_mb, mac, power=None):
    values = {
        "ethernet_interfaces": t(f"{ports} x 10/100 Base-TX Ethernet ports, Auto MDI/MDIX"),
        "management_type": t("Unmanaged, plug-and-play"),
        "dimensions_mm": t(dimensions),
        "switching_capacity_gbps": n(capacity),
        "packet_forwarding_rate_mpps": n(forwarding),
        "packet_buffer_mb": n(buffer_mb),
        "mac_address_table": t(mac),
        "transmission_method": t("Store-and-forward"),
        "installation": t("Desktop or wall mount; rack mount not supported"),
        "operating_temperature_c": t("0 to 45 °C"),
    }
    if power is not None:
        values["max_power_consumption_w"] = n(power)
    return values


PRODUCTS = {
    "S105": {
        "url": "https://www.tendacn.com/product/specification/S105v10",
        "page": "S105 v10.0 Parameter page",
        "title": "Tenda S105 v10.0 official parameters",
        "values": specs(5, "82.0 x 52.0 x 22.3 mm", 1.0, 0.74, 0.055, "1K", 1.6),
    },
    "S108": {
        "url": "https://www.tendacn.com/product/specification/S108V8",
        "page": "S108 v8.0 Parameter page",
        "title": "Tenda S108 v8.0 official parameters",
        "values": specs(8, "124.0 x 59.0 x 23.1 mm", 1.6, 1.19, 0.055, "1K", 2.15),
    },
    "S16": {
        "url": "https://www.tendacn.com/product/specification/S16",
        "page": "S16 Parameter page",
        "title": "Tenda S16 official parameters",
        "values": specs(16, "218.0 x 135.0 x 41.6 mm", 3.2, 2.38, 0.156, "4K"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified current Tenda S105/S108/S16 specifications."
    products = PRODUCTS
    document_version = "Current Tenda official parameter pages; accessed 2026-10-16"
    brand_name = "Tenda"
