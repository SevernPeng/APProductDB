from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    na,
    t,
)


URL_700 = "https://www.downloads.netgear.com/files/GDC/WBE700/WBE700_DS.pdf"
URL_700Y = "https://www.downloads.netgear.com/files/GDC/WBE700Y/WBE700Y_DS.pdf"


COMMON = {
    "supported_bands": t("2.4 GHz / 5 GHz", "Dual-band 2.4 GHz and 5 GHz"),
    "rate_2g_mbps": n(688),
    "total_spatial_streams": n(4, "2x2 at 2.4 GHz plus 2x2 at 5 GHz"),
    "mimo_2g": t("2x2 MU-MIMO"),
    "mimo_5g": t("2x2 MU-MIMO"),
    "rate_6g_mbps": na("Dual-band model; no 6 GHz radio"),
    "mimo_6g": na("Dual-band model; no 6 GHz radio"),
    "max_ssids": n(8, "8 SSID wireless networks per access point"),
    "mesh_support": b(True, "Compatible with all NETGEAR Insight access points"),
    "centralized_management": t("NETGEAR Insight Cloud app/portal; standalone local GUI"),
    "fast_roaming": t("Automatic client steering and automatic roaming in Insight mesh deployments"),
}


PRODUCTS = {
    "WBE700": {
        "url": URL_700,
        "page": "pp. 3-7; technical specifications; document NG_DS_ENT_WBE700_061726",
        "title": "NETGEAR WBE700 WiFi 7 Access Point Data Sheet",
        "values": {
            **COMMON,
            "rate_5g_mbps": n(4332),
            "max_channel_width_mhz": n(240, "5 GHz supports 20/40/80/160/240 MHz"),
            "max_clients": n(150, "Maximum connected clients (idle): 150; maximum active: 75"),
            "ethernet_interfaces": t("1 x 2.5 GbE PoE+ (802.3at) RJ45"),
            "power_method": t("IEEE 802.3at PoE+ or 12 V DC / 2.5 A"),
            "dimensions_mm": t("160 x 160 x 32 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Four internal PIFA antennas: two for 2.4 GHz and two for 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 3.3 dBi; 5 GHz: 3.8 dBi"),
            "wireless_security": t(
                "WPA3 Personal; WPA2 Personal; WPA3/WPA2 mixed mode; SSID isolation; "
                "802.1Q VLAN; MAC filtering"
            ),
            "ip_rating": na("Indoor access point; no ingress-protection rating published"),
        },
    },
    "WBE700Y": {
        "url": URL_700Y,
        "page": "pp. 3-7; technical specifications; document NG_DS_ENT_WBE700Y_080526",
        "title": "NETGEAR WBE700Y Outdoor WiFi 7 Access Point Data Sheet",
        "values": {
            **COMMON,
            "rate_5g_mbps": n(4324),
            "max_channel_width_mhz": n(160),
            "max_clients": n(400, "Maximum associated clients: 400; maximum active: 75"),
            "ethernet_interfaces": t(
                "1 x 2.5 GbE PoE+ RJ45 for power/data; 1 x 2.5 GbE RJ45 data uplink/daisy-chain"
            ),
            "poe_output": na("Second 2.5 GbE port is data-only; no PoE output is specified"),
            "power_method": t("IEEE 802.3at PoE+"),
            "max_power_consumption_w": n(25, "Product page: up to 25 W"),
            "dimensions_mm": t("250 x 182 x 46 mm (W x D x H)"),
            "operating_temperature_c": t("-40 to 55 °C"),
            "antenna_type": t(
                "Internal directional patch arrays plus four included external RP-SMA omnidirectional antennas"
            ),
            "antenna_gain_dbi": t(
                "Internal: approximately 8 dBi (2.4 GHz), 12 dBi (5 GHz); "
                "external: approximately 4 dBi (2.4 GHz), 5 dBi (5 GHz)"
            ),
            "wireless_security": t(
                "WPA3 Personal/Enterprise; WPA3/WPA2 Personal; WPA2 Personal/Enterprise; "
                "WPA2/WPA Personal; Enhanced Open; Open; SSID isolation; 802.1Q VLAN"
            ),
            "ip_rating": t("IP66"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR WBE700 and WBE700Y specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR 2026 product datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
