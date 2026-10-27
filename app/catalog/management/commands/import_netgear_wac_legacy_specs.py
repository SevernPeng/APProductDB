from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "WAC510": {
        "url": "https://www.downloads.netgear.com/files/GDC/WAC510/WAC510_UM_EN.pdf?cid=wmt_netg",
        "page": "pp. 247-249, technical specifications; wireless and management chapters",
        "title": "NETGEAR WAC510 Insight Managed Smart Cloud Wireless Access Point User Manual",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz (concurrent dual-band)"),
            "rate_2g_mbps": n(400),
            "rate_5g_mbps": n(867),
            "total_spatial_streams": n(4, "2 spatial streams per concurrent radio"),
            "mimo_2g": t("2x2 SU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz: 20/40 MHz; 5 GHz: 20/40/80 MHz"),
            "max_clients": n(200, "Maximum 200 clients per radio and 200 total per access point"),
            "ethernet_interfaces": t("1 x Gigabit WAN/PoE RJ45; 1 x Gigabit LAN RJ45"),
            "power_method": t("IEEE 802.3af PoE or optional 12 V DC adapter"),
            "max_power_consumption_w": n(9.3),
            "dimensions_mm": t("197.32 x 197.32 x 37 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Internal antennas for two 2x2 radios"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 4 dBi"),
            "centralized_management": t("NETGEAR Insight app/cloud portal or standalone local web GUI"),
            "fast_roaming": t("802.11k radio resource management and 802.11v band steering"),
            "wireless_security": t(
                "WPA3-Personal; WPA3/WPA2-Personal; WPA2-Personal; "
                "WPA2/WPA-Personal; WPA2-Enterprise"
            ),
        },
    },
    "WAC730": {
        "url": "https://www.downloads.netgear.com/files/GDC/WAC720/WAC720_730_RM_10Oct2015.pdf",
        "page": "technical specifications and wireless configuration chapters",
        "title": "NETGEAR WAC720/WAC730 ProSAFE Wireless Access Point Reference Manual",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz (concurrent dual-band)"),
            "rate_2g_mbps": n(450),
            "rate_5g_mbps": n(1300),
            "total_spatial_streams": n(6, "3 spatial streams per concurrent radio"),
            "mimo_2g": t("3x3 SU-MIMO"),
            "mimo_5g": t("3x3 SU-MIMO"),
            "max_channel_width_mhz": n(80),
            "ethernet_interfaces": t("1 x Gigabit PoE RJ45; 1 x RJ45 console port"),
            "power_method": t("IEEE 802.3af/802.3at PoE or 12 V DC adapter"),
            "max_power_consumption_w": n(12.9),
            "dimensions_mm": t("197 x 197 x 40 mm (W x D x H)"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t(
                "Three internal dual-band antennas plus three reverse-SMA connectors for optional external antennas"
            ),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 6 dBi"),
            "centralized_management": t(
                "Standalone; Ensemble management for up to 10 access points; "
                "WC7600/WC9500 controller; NETGEAR Business Central cloud"
            ),
            "wireless_security": t(
                "WPA/WPA2; 802.1X RADIUS with EAP-TLS/EAP-TTLS/PEAP; "
                "rogue AP detection; MAC access control"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR WAC510 and WAC730 specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR manuals and datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
