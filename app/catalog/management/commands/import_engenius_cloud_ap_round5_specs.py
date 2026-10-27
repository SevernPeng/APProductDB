from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


BASE = "https://www.engeniustech.com/in/products/wireless/indoor-access-points"


def values(*, clients, ethernet, mimo, streams, temperature, poe_output=None):
    result = {
        "max_clients": n(clients, "Maximum concurrent users"),
        "ethernet_interfaces": t(ethernet),
        "operating_temperature_c": t(temperature),
        "mimo_2g": t(mimo),
        "mimo_5g": t(mimo),
        "total_spatial_streams": n(streams, "Sum of published spatial streams across concurrent serving radios"),
    }
    if streams > 4:
        result["mimo_6g"] = t(mimo)
    if poe_output:
        result["poe_output"] = t(poe_output)
    return result


PRODUCTS = {
    "ECW515": {
        "url": f"{BASE}/ecw515/",
        "page": "Technical Specifications and data sheet v1.2 dated 2026-02-12",
        "title": "EnGenius ECW515 official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 2.5 Gigabit Ethernet PoE+ uplink; 4 x Gigabit Ethernet LAN ports; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=4,
            temperature="0 to 40 °C",
            poe_output="Gigabit Ethernet PoE output for a VoIP phone or other PoE device",
        ),
    },
    "ECW520": {
        "url": f"{BASE}/ecw520/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW520 official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 2.5 Gigabit Ethernet PoE+ port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=6,
            temperature="0 to 40 °C",
        ),
    },
    "ECW526": {
        "url": f"{BASE}/ecw526/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW526 official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 10 Gigabit Ethernet PoE+ port; 1 x DC jack",
            mimo="2x2:2 SU-MIMO and MU-MIMO",
            streams=6,
            temperature="0 to 50 °C",
        ),
    },
    "ECW536": {
        "url": f"{BASE}/ecw536/",
        "page": "Technical Specifications",
        "title": "EnGenius ECW536 official product specifications",
        "values": values(
            clients=512,
            ethernet="1 x 10 Gigabit Ethernet PoE++ port; 1 x 10 Gigabit Ethernet port; 1 x DC jack",
            mimo="4x4:4 SU-MIMO and MU-MIMO",
            streams=12,
            temperature="0 to 50 °C",
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified EnGenius ECW515/520/526/536 AP specifications."
    products = PRODUCTS
    document_version = "Current EnGenius official product pages and listed data sheets; accessed 2026-10-16"
    brand_name = "EnGenius"
