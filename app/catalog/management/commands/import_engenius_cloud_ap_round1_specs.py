from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


BASE = "https://www.engeniustech.com/in/products/wireless/indoor-access-points"


def dual_radio_values(*, clients, ethernet, mimo, streams, temperature="0 to 40 °C"):
    return {
        "max_clients": n(clients, f"Maximum concurrent users: {clients} per radio"),
        "ethernet_interfaces": t(ethernet),
        "operating_temperature_c": t(temperature),
        "mimo_2g": t(mimo),
        "mimo_5g": t(mimo),
        "total_spatial_streams": n(streams, "Sum of published spatial streams across the two concurrent radios"),
    }


PRODUCTS = {
    "ECW120": {
        "url": f"{BASE}/ecw120/",
        "page": "Technical Specifications: interfaces, radio chains, concurrent users and environmental specifications",
        "title": "EnGenius ECW120 official product specifications",
        "values": dual_radio_values(
            clients=128,
            ethernet="1 x Gigabit Ethernet PoE port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO; 5 GHz also supports 2-stream MU-MIMO",
            streams=4,
        ),
    },
    "ECW210L": {
        "url": f"{BASE}/ecw210l/",
        "page": "Technical Specifications: interfaces, radio chains, concurrent users and environmental specifications; data sheet v1.2",
        "title": "EnGenius ECW210L official product specifications",
        "values": dual_radio_values(
            clients=128,
            ethernet="1 x Gigabit Ethernet PoE port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=4,
        ),
    },
    "ECW220": {
        "url": f"{BASE}/ecw220/",
        "page": "Technical Specifications: interfaces, radio chains, concurrent users and environmental specifications",
        "title": "EnGenius ECW220 official product specifications",
        "values": dual_radio_values(
            clients=512,
            ethernet="1 x Gigabit Ethernet PoE port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=4,
        ),
    },
    "ECW230": {
        "url": f"{BASE}/ecw230/",
        "page": "Technical Specifications: interfaces, radio chains, concurrent users and environmental specifications",
        "title": "EnGenius ECW230 official product specifications",
        "values": dual_radio_values(
            clients=512,
            ethernet="1 x 2.5 Gigabit Ethernet PoE+ port; 1 x DC jack",
            mimo="4x4:4 SU-MIMO and MU-MIMO",
            streams=8,
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW120/210L/220/230 AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
