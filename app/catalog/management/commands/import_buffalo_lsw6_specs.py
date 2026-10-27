from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


def values(ports, dimensions, capacity, forwarding, buffer_mb, mac, power):
    return {
        "ethernet_interfaces": t(f"{ports} x 10/100/1000 Mbps RJ45 ports"),
        "management_type": t("Unmanaged"),
        "fanless": b(True),
        "loop_prevention": b(True, "Loop detection supported"),
        "flow_control": t("IEEE 802.3x flow control and half-duplex backpressure"),
        "switching_capacity_gbps": n(capacity),
        "packet_forwarding_rate_mpps": n(forwarding),
        "packet_buffer_mb": n(buffer_mb),
        "mac_address_table": t(mac),
        "max_power_consumption_w": n(power),
        "transmission_method": t("Store-and-forward"),
        "dimensions_mm": t(dimensions),
        "installation": t("Desktop, wall mount, and rear magnet"),
        "operating_temperature_c": t("0 to 40 °C"),
    }


PRODUCTS = {
    "LSW6-GT-5ESL": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-5esl_nbk.html",
        "page": "Official product specifications, LSW6-GT-5ESL/NBK",
        "title": "Buffalo LSW6-GT-5ESL/NBK official specifications",
        "values": values(5, "121 x 26 x 75 mm", 10, 7.44, 0.125, "2K", 3.3),
    },
    "LSW6-GT-8ESL": {
        "url": "https://www.buffalo.jp/product/detail/lsw6-gt-8esl_nbk.html",
        "page": "Official product specifications, LSW6-GT-8ESL/NBK",
        "title": "Buffalo LSW6-GT-8ESL/NBK official specifications",
        "values": values(8, "154 x 26 x 85 mm", 16, 11.905, 0.188, "4K", 5.3),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Buffalo LSW6-GT ESL-series specifications."
    products = PRODUCTS
    document_version = "Current Buffalo Japan official product pages; accessed 2026-10-16"
    brand_name = "Buffalo"
