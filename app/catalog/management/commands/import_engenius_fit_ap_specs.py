from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


INDOOR = "https://www.engeniustech.com/in/products/wireless/indoor-access-points"
OUTDOOR = "https://www.engeniustech.com/in/products/wireless/outdoor-access-points"


def fit_values(*, clients, ethernet, rate_2g, rate_5g, mimo, streams, temperature, width=None):
    values = {
        "max_clients": n(clients, "Maximum concurrent users per radio"),
        "ethernet_interfaces": t(ethernet),
        "rate_2g_mbps": n(rate_2g),
        "rate_5g_mbps": n(rate_5g),
        "mimo_2g": t(mimo),
        "mimo_5g": t(mimo),
        "total_spatial_streams": n(streams, "Sum of published spatial streams across both concurrent radios"),
        "operating_temperature_c": t(temperature),
    }
    if width is not None:
        values["max_channel_width_mhz"] = n(width)
    return values


PRODUCTS = {
    "EWS276-FIT": {
        "url": f"{INDOOR}/ews276-fit/",
        "page": "Technical Specifications and model comparison",
        "title": "EnGenius EWS276-FIT official product specifications",
        "values": fit_values(
            clients=128,
            ethernet="1 x 2.5 Gigabit Ethernet port; 1 x 12 V DC input",
            rate_2g=1148,
            rate_5g=2400,
            mimo="4x4:4 SU-MIMO and MU-MIMO",
            streams=8,
            temperature="0 to 40 °C",
            width=80,
        ),
    },
    "EWS356-FIT": {
        "url": f"{INDOOR}/ews356-fit/",
        "page": "Technical Specifications and data sheet v1.3 dated 2025-04-21",
        "title": "EnGenius EWS356-FIT official product specifications",
        "values": fit_values(
            clients=128,
            ethernet="1 x Gigabit Ethernet port; 1 x 12 V DC input",
            rate_2g=574,
            rate_5g=2400,
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=4,
            temperature="0 to 40 °C",
        ),
    },
    "EWS357-FIT": {
        "url": f"{INDOOR}/ews357-fit/",
        "page": "Technical Specifications and data sheet v1.0 dated 2023-12-05",
        "title": "EnGenius EWS357-FIT official product specifications",
        "values": fit_values(
            clients=128,
            ethernet="1 x Gigabit Ethernet port; 1 x 12 V DC input",
            rate_2g=574,
            rate_5g=1200,
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=4,
            temperature="0 to 40 °C",
        ),
    },
    "EWS850-FIT": {
        "url": f"{OUTDOOR}/ews850-fit/",
        "page": "Technical Specifications and data sheet v1.1 dated 2025-03-11",
        "title": "EnGenius EWS850-FIT official product specifications",
        "values": {
            **fit_values(
                clients=128,
                ethernet="1 x 2.5 Gigabit Ethernet PoE+ port",
                rate_2g=574,
                rate_5g=1200,
                mimo="2x2:2 SU-MIMO and MU-MIMO",
                streams=4,
                temperature="-20 to 60 °C",
            ),
            "lightning_protection_kv": t("1 kV surge protection"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius Fit access-point specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and latest listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
