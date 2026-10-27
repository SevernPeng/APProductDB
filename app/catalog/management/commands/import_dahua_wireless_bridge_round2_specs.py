from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PFM886_VALUES = {
    "supported_bands": t("5 GHz"),
    "rate_5g_mbps": n(867),
    "max_channel_width_mhz": n(80),
    "antenna_type": t("Integrated directional antenna"),
    "antenna_gain_dbi": t("23 dBi"),
    "beamwidth": t("Horizontal 10°; vertical 10°"),
    "wireless_range": t("Up to 15 km"),
    "ethernet_interfaces": t("1 x 10/100/1000Base-T RJ45 port"),
    "poe_input": t("PoE input via PoE switch or PoE adapter"),
    "max_power_consumption_w": n(25),
    "bridge_modes": t("Access point, client, WDS AP, WDS client and WDS repeater; route or bridge"),
    "centralized_management": t("Web, SNMP and access controller"),
    "wireless_security": t("802.1X, WPA-PSK and WPA2-PSK; IP/MAC filtering and hidden SSID"),
    "operating_temperature_c": t("-30 to 70 °C"),
    "dimensions_mm": t("240 mm x Ø373 mm"),
    "ip_rating": t("IP66"),
}

PFWB_VALUES = {
    "supported_bands": t("5 GHz"),
    "rate_5g_mbps": n(866),
    "max_channel_width_mhz": n(80),
    "antenna_type": t("Integrated directional panel antenna, dual-linear polarization"),
    "antenna_gain_dbi": t("18 dBi"),
    "beamwidth": t("Azimuth 90°; elevation 20°"),
    "wireless_range": t("Recommended 0 to 5 km; maximum at least 7 km"),
    "ethernet_interfaces": t("1 x 10/100/1000Base-T RJ45 port"),
    "poe_input": t("12 to 24 VDC passive PoE; 24 V adapter included"),
    "max_power_consumption_w": n(10),
    "bridge_modes": t("AP auto-WDS/TDMA; station WDS/TDMA/ARP-NAT; IPv4/IPv6 router or bridge"),
    "centralized_management": t("HTTPS web UI, SSH, SNMP, Telnet, Syslog and DWMP"),
    "wireless_security": t("WPA/WPA2 Personal and Enterprise, WACL and user isolation"),
    "operating_temperature_c": t("-30 to 70 °C"),
    "dimensions_mm": t("383 x 100 x 98 mm"),
    "ip_rating": t("IP66"),
}


PRODUCTS = {
    "DH-PFM886-15": {
        "url": "https://www.dahuasecurity.com/uk/products/discontinued-products/transmission/pfm886-15",
        "page": "Official EOL product specifications; model listed as DH-PFM886-15",
        "title": "Dahua DH-PFM886-15 official specifications",
        "values": PFM886_VALUES,
    },
    "PFM886-15": {
        "url": "https://www.dahuasecurity.com/uk/products/discontinued-products/transmission/pfm886-15",
        "page": "Official EOL product specifications; model listed as DH-PFM886-15",
        "title": "Dahua PFM886-15 official specifications",
        "values": PFM886_VALUES,
    },
    "DH-PFWB5-90ac": {
        "url": "https://www.dahuasecurity.com/asset/upload/product/20180803/DH-PFWB5-90ac_Datasheet_20180803.pdf",
        "page": "Official datasheet, pages 1-2",
        "title": "Dahua DH-PFWB5-90ac official datasheet",
        "values": PFWB_VALUES,
    },
    "PFWB5-90ac": {
        "url": "https://www.dahuasecurity.com/asset/upload/product/20180803/DH-PFWB5-90ac_Datasheet_20180803.pdf",
        "page": "Official datasheet, pages 1-2; model listed as DH-PFWB5-90ac",
        "title": "Dahua PFWB5-90ac official datasheet",
        "values": PFWB_VALUES,
    },
    "PFM885-I": {
        "url": "https://www.dahuasecurity.com/in/products/transmission/wireless-devices/other-wireless-bridge/pfm885-i",
        "page": "Official product specifications and linked datasheet",
        "title": "Dahua PFM885-I official specifications",
        "values": {
            "supported_bands": t("2.4 GHz"),
            "rate_2g_mbps": n(300),
            "max_channel_width_mhz": n(40),
            "antenna_type": t("Internal directional antenna"),
            "antenna_gain_dbi": t("6 dBi"),
            "beamwidth": t("Horizontal 65°; vertical 60°"),
            "wireless_range": t("Up to 500 m"),
            "ethernet_interfaces": t("2 x LAN RJ45 ports"),
            "poe_input": t("48 V / 0.25 A passive PoE or 12 VDC"),
            "max_power_consumption_w": n(8),
            "bridge_modes": t("Access point, client, WDS AP and WDS client; route or bridge"),
            "centralized_management": t("Web, access controller, SNMP, Telnet and Syslog"),
            "wireless_security": t("WPA-PSK/WPA2, CCMP-AES/TKIP, IP/MAC filtering and hidden SSID"),
            "operating_temperature_c": t("-30 to 70 °C"),
            "dimensions_mm": t("150 x 150 x 32 mm"),
            "ip_rating": t("IP41"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified legacy Dahua PFM/PFWB wireless-bridge specifications."
    products = PRODUCTS
    document_version = "Dahua official product pages and datasheets; accessed 2026-10-16"
    brand_name = "Dahua"
