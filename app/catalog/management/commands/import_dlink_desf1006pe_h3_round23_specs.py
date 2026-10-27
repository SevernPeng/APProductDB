from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = (
    "https://www.dlink.com.vn/products/"
    "des-f1006p-e-250m-6-port-10-100-switch-with-4-poe-ports-and-2-uplink-ports-des-f1006p-e"
)


PRODUCTS = {
    "DES-F1006P-E": {
        "url": SOURCE_URL,
        "page": "Tech Specifications, Hardware Version H3",
        "title": "D-Link DES-F1006P-E Current Product Page",
        "values": {
            "poe_standard": t(
                "IEEE 802.3af / 802.3at / 802.3bt",
                "H3: ports 1-3 support 802.3af/at; port 4 supports 802.3af/at/bt up to 60 W",
            ),
            "max_poe_per_port_w": n(
                60,
                "H3 port 4 supports up to 60 W via IEEE 802.3bt",
            ),
            "max_power_consumption_w": n(
                65,
                "H3 maximum power consumption: 65 W with PoE on",
            ),
            "mac_address_table": t("2K entries", "H3 MAC address table size: 2K entries"),
            "packet_buffer_mb": n(
                0.125,
                "H3 packet buffer: 1 Mbit = 0.125 MB",
            ),
            "transmission_method": t("Store-and-forward", "H3 transmission method: Store-and-forward"),
            "fanless": b(True, "H3 ventilation: Fanless"),
            "lightning_protection_kv": t("6 kV", "H3: 6 kV lightning protection"),
            "operating_temperature_c": t("0 to 40 °C", "H3 operating temperature: 0 °C to 40 °C"),
            "dimensions_mm": t(
                "190 x 131 x 40 mm (L x W x H)",
                "H3 dimensions: 190 x 131 x 40 mm (L x W x H); official page has a unit typo on height",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Update D-Link DES-F1006P-E to the current H3 hardware specifications."
    products = PRODUCTS
    document_version = "Current official D-Link DES-F1006P-E hardware version H3 page; accessed 2026-10-27"
    brand_name = "D-Link"
