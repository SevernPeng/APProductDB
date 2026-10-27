from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


PRODUCTS = {
    "GWN7602": {
        "url": "https://www.grandstream.com/hubfs/Product_Documentation/datasheet_gwn7602_english.pdf",
        "page": "Technical specifications, document 4.2021.01",
        "title": "Grandstream GWN7602 official datasheet",
        "values": {
            "max_clients": n(80),
            "ethernet_interfaces": t("1 x Gigabit Ethernet PoE/PoE+ uplink; 2 x 100 Mbps Ethernet PSE ports; 1 x 100 Mbps Ethernet port"),
            "rate_2g_mbps": n(300),
            "rate_5g_mbps": n(867),
            "mimo_2g": t("2x2:2 MIMO"),
            "operating_temperature_c": t("0 to 40 °C"),
            "max_power_consumption_w": n(20),
            "poe_output": t("Two 100 Mbps PSE ports, maximum 6 W output per port"),
            "fast_roaming": t("Supported", "Grandstream GWN76xx fast-roaming feature"),
        },
    },
    "GWN7603": {
        "url": "https://documentation.grandstream.com/knowledge-base/gwn7603-technical-specifications/",
        "page": "GWN7603 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7603 official technical specifications",
        "values": {
            "max_clients": n(100, "100+ concurrent clients"),
            "ethernet_interfaces": t("1 x Gigabit Ethernet PoE/PoE+ uplink; 2 x Gigabit Ethernet PSE ports; 1 x Gigabit Ethernet port"),
            "rate_2g_mbps": n(400, "Maximum with 256-QAM"),
            "rate_5g_mbps": n(867),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "operating_temperature_c": t("0 to 40 °C"),
            "max_power_consumption_w": n(20),
            "poe_output": t("Two Gigabit Ethernet PSE ports, maximum 6 W output per port"),
            "max_channel_width_mhz": n(80),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
            "centralized_management": t("GDMS Networking cloud; GWN Manager on-premises; embedded controller"),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
        },
    },
    "GWN7605": {
        "url": "https://documentation.grandstream.com/knowledge-base/gwn7605-technical-specifications/",
        "page": "GWN7605 Technical Specifications, updated 2026",
        "title": "Grandstream GWN7605 official technical specifications",
        "values": {
            "ethernet_interfaces": t("2 x autosensing 10/100/1000 Base-T Ethernet ports"),
            "rate_2g_mbps": n(300),
            "rate_5g_mbps": n(867),
            "mimo_2g": t("2x2:2 MIMO"),
            "operating_temperature_c": t("0 to 40 °C"),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
    "GWN7605LR": {
        "url": "https://documentation.grandstream.com/knowledge-base/gwn7605lr-technical-specifications/",
        "page": "GWN7605LR Technical Specifications, updated 2026",
        "title": "Grandstream GWN7605LR official technical specifications",
        "values": {
            "rate_2g_mbps": n(300),
            "rate_5g_mbps": n(867),
            "operating_temperature_c": t("-30 to 70 °C"),
            "fast_roaming": t("802.11k/v/r", "Voice Enterprise fast roaming supported by GWN76xx series"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7602/7603/7605/7605LR specifications."
    products = PRODUCTS
    document_version = "Current Grandstream official datasheets and technical documentation; accessed 2026-10-16"
    brand_name = "Grandstream"
