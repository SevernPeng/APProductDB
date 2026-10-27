from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


COMMON_VALUES = {
    "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
    "rate_2g_mbps": n(1147),
    "rate_5g_mbps": n(5765),
    "rate_6g_mbps": n(11530),
    "total_spatial_streams": n(12, "Three concurrent 4x4 radios"),
    "mimo_2g": t("4x4 bidirectional MU-MIMO"),
    "mimo_5g": t("4x4 bidirectional MU-MIMO"),
    "mimo_6g": t("4x4 bidirectional MU-MIMO"),
    "max_channel_width_mhz": n(320),
    "ethernet_interfaces": t("1 x 100M/1G/2.5G/5G/10GBASE-T PoE++ RJ45"),
    "power_method": t("IEEE 802.3bt PoE++"),
    "max_power_consumption_w": n(39),
    "dimensions_mm": t("172 x 172 x 44 mm (W x D x H)"),
    "operating_temperature_c": t("0 to 40 °C"),
    "antenna_type": t("Integrated omnidirectional antennas for three 4x4 radios"),
    "antenna_gain_dbi": t("2.4 GHz: 3.45 dBi; 5 GHz: 5.39 dBi; 6 GHz: 5.49 dBi"),
    "centralized_management": t("NETGEAR Insight Cloud app/portal and local network management"),
    "mesh_support": b(True, "Instant WiFi Mesh with NETGEAR Insight managed access points"),
    "fast_roaming": t("Fast roaming: Yes"),
    "max_ssids": n(8),
    "wireless_security": t(
        "OWE; WPA2-PSK; WPA3-PSK; WPA2-Enterprise; WPA3-Enterprise; "
        "dynamic VLAN and 802.1Q VLAN"
    ),
}


PRODUCTS = {
    "WBE750": {
        "url": "https://www.netgear.com/business/wifi/access-points/wbe750/",
        "page": "Current product specifications and official datasheet",
        "title": "NETGEAR WBE750 Insight Managed WiFi 7 Access Point",
        "values": COMMON_VALUES,
    },
    "WBE758": {
        "url": "https://www.netgear.com/business/wifi/access-points/wbe758/",
        "page": "Current product specifications and official datasheet",
        "title": "NETGEAR WBE758 Insight Managed WiFi 7 Access Point",
        "values": COMMON_VALUES,
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR WBE750 and WBE758 specifications."
    products = PRODUCTS
    document_version = "Current official NETGEAR product pages and datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
