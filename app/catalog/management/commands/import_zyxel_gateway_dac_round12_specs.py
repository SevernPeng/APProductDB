from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    na,
    t,
)


VPN300_SOURCE = "https://www.zyxel.com/library/download/Firewall-Comparison-Matrix.pdf"
SWITCH_GUIDE = (
    "https://www.zyxel.com/sites/zyxel/files/library/assets/tech-library/"
    "quick-sales-guide/qsg_switch_2025.pdf"
)


def dac_values(connector, voltage):
    return {
        "accessory_connector_type": t(connector),
        "accessory_input_power": t(f"{voltage} DC; maximum current 150 mA"),
        "accessory_fiber_mode": na("Direct-attach copper cable; optical fiber mode is not applicable"),
        "accessory_wavelength_nm": na("Direct-attach copper cable; optical wavelength is not applicable"),
    }


PRODUCTS = {
    "VPN300": {
        "url": VPN300_SOURCE,
        "page": "Advanced ZyWALL VPN Firewalls comparison table, VPN300 column",
        "title": "Zyxel Firewall Comparison Matrix",
        "values": {
            "routing_throughput_mbps": n(
                2600,
                "SPI firewall throughput: 2,600 Mbps; stored in the routing/firewall "
                "throughput field and not duplicated as NAT throughput",
            ),
        },
    },
    "DAC10G-1M": {
        "url": SWITCH_GUIDE,
        "page": "p. 29, Direct Attached Cable 10G Series table",
        "title": "Zyxel Switch Quick Sales Guide 2025",
        "values": dac_values("SFP+ to SFP+", "3.14-3.46 V"),
    },
    "DAC10G-3M": {
        "url": SWITCH_GUIDE,
        "page": "p. 29, Direct Attached Cable 10G Series table",
        "title": "Zyxel Switch Quick Sales Guide 2025",
        "values": dac_values("SFP+ to SFP+", "3.14-3.46 V"),
    },
    "DAC25G-1M": {
        "url": SWITCH_GUIDE,
        "page": "p. 30, Direct Attached Cable 25G Series table",
        "title": "Zyxel Switch Quick Sales Guide 2025",
        "values": dac_values("SFP28 to SFP28", "3.135-3.465 V"),
    },
    "DAC100G-1M": {
        "url": SWITCH_GUIDE,
        "page": "p. 30, Direct Attached Cable 100G Series table",
        "title": "Zyxel Switch Quick Sales Guide 2025",
        "values": dac_values("QSFP28 to QSFP28", "3.135-3.465 V"),
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified Zyxel VPN300 firewall throughput and current DAC specifications."
    products = PRODUCTS
    document_version = "Official Zyxel comparison matrix and Switch Quick Sales Guide 2025; accessed 2026-10-23"
    brand_name = "Zyxel"
