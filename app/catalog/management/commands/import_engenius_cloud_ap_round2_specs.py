from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


INDOOR = "https://www.engeniustech.com/in/products/wireless/indoor-access-points"
OUTDOOR = "https://www.engeniustech.com/in/products/wireless/outdoor-access-points"


def values(*, clients, ethernet, mimo, temperature, streams=None, **extra):
    result = {
        "max_clients": n(clients, f"Maximum concurrent users: {clients} per radio"),
        "ethernet_interfaces": t(ethernet),
        "operating_temperature_c": t(temperature),
        "mimo_2g": t(mimo),
        "mimo_5g": t(mimo),
        **extra,
    }
    if streams is not None:
        result["total_spatial_streams"] = n(
            streams, "Sum of published spatial streams across the two concurrent radios"
        )
    return result


PRODUCTS = {
    "ECW220S": {
        "url": f"{INDOOR}/ecw220s/",
        "page": "Technical Specifications and data sheet v1.0",
        "title": "EnGenius ECW220S official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x Gigabit Ethernet PoE+ port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            temperature="0 to 40 °C",
            streams=4,
        ),
    },
    "ECW230S": {
        "url": f"{INDOOR}/ecw230s/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW230S official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 2.5 Gigabit Ethernet PoE+ port; 1 x DC jack",
            mimo="4x4:4 SU-MIMO and MU-MIMO",
            temperature="0 to 40 °C",
        ),
    },
    "ECW215": {
        "url": f"{INDOOR}/ecw215/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW215 official product specifications",
        "values": values(
            clients=128,
            ethernet="2 x Gigabit Ethernet PoE+ ports; 1 x Gigabit Ethernet PSE-out port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            temperature="0 to 40 °C",
        ),
    },
    "ECW260": {
        "url": f"{OUTDOOR}/ecw260/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW260 official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 2.5 Gigabit Ethernet PoE+ port",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            temperature="-20 to 60 °C",
            streams=4,
            lightning_protection_kv=t("1 kV surge protection"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW215/220S/230S/260 AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
