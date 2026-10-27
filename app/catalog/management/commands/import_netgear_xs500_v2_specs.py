from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_505 = "https://www.netgear.com/sg/business/wired/switches/unmanaged/xs505mv2/"
URL_508 = "https://www.netgear.com/sg/business/wired/switches/unmanaged/xs508mv2/"


def item(model, url, ports, power, mtbf):
    capacity = ports * 20
    return {
        "url": url,
        "page": "Current product page, Product Specifications",
        "title": f"NETGEAR {model}v2 current product page",
        "values": {
            "ethernet_interfaces": t(
                f"{ports} x 100M/1G/2.5G/5G/10G auto-sensing copper ports",
                f"{ports} x 10G/Multi-Gigabit copper ports; no SFP port in v2",
            ),
            "management_type": t("Unmanaged, instant plug-and-play"),
            "switching_capacity_gbps": n(capacity, f"Non-blocking full duplex across {ports} x 10 Gbps ports: {capacity} Gbps"),
            "mac_address_table": t("16K entries"),
            "packet_buffer_mb": n("1.5"),
            "jumbo_frame_bytes": n(12000, "Up to 12K bytes"),
            "qos_support": t("IEEE 802.1p QoS"),
            "fanless": b(False, "1 active low-noise fan"),
            "installation": t("Desktop"),
            "max_power_consumption_w": n(power),
            "dimensions_mm": t("210 x 140 x 40 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    }


PRODUCTS = {
    "XS505M": item("XS505M", URL_505, 5, 26, 944360),
    "XS508M": item("XS508M", URL_508, 8, 39, 519995),
}


class Command(VerifiedImportCommand):
    help = "Import current NETGEAR XS505Mv2 and XS508Mv2 specifications into the canonical family records."
    products = PRODUCTS
    document_version = "Current official NETGEAR XS505Mv2/XS508Mv2 product pages; accessed 2026-10-20"
    brand_name = "NETGEAR"
