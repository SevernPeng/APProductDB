from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    na,
    t,
)


DUAL_VALUES = {
    "supported_bands": t("2.4 GHz / 5 GHz"),
    "rate_2g_mbps": n(688),
    "rate_5g_mbps": n(2882),
    "rate_6g_mbps": na("Dual-band model; no 6 GHz radio"),
    "total_spatial_streams": n(4),
    "mimo_2g": t("2x2 MU-MIMO"),
    "mimo_5g": t("2x2 MU-MIMO"),
    "mimo_6g": na("Dual-band model; no 6 GHz radio"),
    "max_channel_width_mhz": n(160),
    "max_clients": n(75),
    "max_ssids": n(8),
    "ethernet_interfaces": t("1 x 2.5 GbE PoE+ (802.3at) RJ45"),
    "power_method": t("IEEE 802.3at PoE+ or 12 V DC / 2.5 A"),
    "dimensions_mm": t("160 x 160 x 32 mm (W x D x H)"),
    "operating_temperature_c": t("0 to 40 °C"),
    "centralized_management": t("NETGEAR Insight Cloud; NETGEAR Engage; standalone local GUI"),
    "mesh_support": b(True, "Compatible with NETGEAR Engage or Insight managed access points"),
    "wireless_security": t("WPA3; WPA2; SSID isolation and 802.1Q VLAN support"),
}


TRI_VALUES = {
    "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
    "rate_2g_mbps": n(688),
    "rate_5g_mbps": n(2882),
    "rate_6g_mbps": n(5765),
    "total_spatial_streams": n(6),
    "mimo_2g": t("2x2 bidirectional MU-MIMO"),
    "mimo_5g": t("2x2 bidirectional MU-MIMO"),
    "mimo_6g": t("2x2 bidirectional MU-MIMO"),
    "max_channel_width_mhz": n(320),
    "max_ssids": n(8),
    "ethernet_interfaces": t("1 x 100M/1G/2.5GBASE-T PoE+ RJ45"),
    "power_method": t("IEEE 802.3at PoE+; 12 V DC / 2.5 A supported"),
    "max_power_consumption_w": n(25),
    "dimensions_mm": t("157 x 157 x 40 mm (W x D x H)"),
    "operating_temperature_c": t("0 to 40 °C"),
    "antenna_type": t("Integrated omnidirectional antennas for three 2x2 radios"),
    "antenna_gain_dbi": t("2.4 GHz: 3.45 dBi; 5 GHz: 5.39 dBi; 6 GHz: 5.49 dBi"),
    "centralized_management": t("NETGEAR Insight Cloud app/portal and local network management"),
    "mesh_support": b(True, "Instant WiFi Mesh wireless backhaul"),
    "fast_roaming": t("Fast roaming: Yes"),
    "wireless_security": t(
        "OWE; WPA2-PSK; WPA3-PSK; WPA2-Enterprise; WPA3-Enterprise; "
        "dynamic VLAN and 802.1Q VLAN"
    ),
}


PRODUCTS = {
    "WBE708": {
        "url": "https://www.netgear.com/ca-en/business/wifi/access-points/wbe708/",
        "page": "Current official product specifications",
        "title": "NETGEAR WBE708 Engage Managed WiFi 7 Access Point",
        "values": DUAL_VALUES,
    },
    "WBE710": {
        "url": "https://www.netgear.com/business/wifi/access-points/wbe710/",
        "page": "Current product specifications and official datasheet",
        "title": "NETGEAR WBE710 Insight Managed WiFi 7 Access Point",
        "values": {**TRI_VALUES, "max_clients": n(600, "200 users per radio; 600 total")},
    },
    "WBE718": {
        "url": "https://www.downloads.netgear.com/files/GDC/WBE718/WBE718_DS.pdf",
        "page": "pp. 1-8, technical specifications",
        "title": "NETGEAR WBE718 Insight Managed WiFi 7 Access Point Data Sheet",
        "values": TRI_VALUES,
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR WBE708, WBE710, and WBE718 specifications."
    products = PRODUCTS
    document_version = "Current official NETGEAR product pages and datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
