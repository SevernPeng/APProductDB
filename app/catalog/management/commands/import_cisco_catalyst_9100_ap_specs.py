from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_9105 = "https://www.cisco.com/c/en/us/products/collateral/wireless/catalyst-9100ax-access-points/datasheet-c78-744062.html"
URL_9115 = "https://www.cisco.com/c/en/us/products/collateral/wireless/catalyst-9100ax-access-points/datasheet-c78-741988.pdf"
URL_9120 = "https://www.cisco.com/c/en/us/products/collateral/wireless/catalyst-9120ax-series-access-points/datasheet-c78-742115.html"
URL_9124 = "https://www.cisco.com/c/en/us/products/collateral/wireless/catalyst-9100ax-access-points/nb-06-cat9124-ser-ap-ds-cte-en.html"


COMMON_SECURITY = t("WPA3, WPA2, WPA, 802.1X and AES; enterprise EAP methods")


PRODUCTS = {
    "C9105AXI": {
        "url": URL_9105,
        "page": "Product specifications and Catalyst 9105AXI deployment-guide key features",
        "title": "Cisco Catalyst 9105 Series Access Points Data Sheet (updated 2022-11-03)",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "dimensions_mm": t("150 x 150 x 30 mm (W x L x H), excluding bracket"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T uplink; 1 x RJ-45 management console"),
            "max_clients": n(200, "Cisco deployment guide states support for up to 200 Wi-Fi devices"),
            "mimo_2g": t("2x2:2 uplink/downlink MU-MIMO"),
            "mimo_5g": t("2x2:2 uplink/downlink MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C; above 40 °C the 2.4 GHz radio reduces to 1x1"),
            "power_method": t("802.3af PoE; 802.3at PoE+ / Cisco UPOE; AIR-PWRINJ5 or AIR-PWRINJ6 injector"),
            "wireless_security": COMMON_SECURITY,
            "centralized_management": t(
                "Cisco Catalyst 9800, 3504, 5520, 8540 and virtual wireless controllers; Cisco DNA Center"
            ),
        },
    },
    "C9115AXI": {
        "url": URL_9115,
        "page": "pp. 6-9 product specifications",
        "title": "Cisco Catalyst 9115 Series Wi-Fi 6 Access Points Data Sheet (2023)",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 4 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": t(
                "Cisco Catalyst 9800, 3500, 5520, 8540 and virtual wireless controllers; Cisco DNA Center"
            ),
            "dimensions_mm": t("203 x 203 x 38 mm (W x L x H), excluding bracket"),
            "ethernet_interfaces": t("1 x 100/1000/2500 Multigigabit Ethernet; RJ-45 console; USB 2.0"),
            "max_power_consumption_w": n(20.4, "Maximum PoE consumption at full features with 802.3at"),
            "mimo_2g": t("4x4:4 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C; above 40 °C both radios reduce from 4x4 to 2x2"),
            "power_method": t("802.3af PoE (reduced features); 802.3at PoE+ / Cisco UPOE for full features"),
            "rate_2g_mbps": n(574, "4x4 802.11ax PHY rate at 20 MHz; part of the official 5.38 Gbps aggregate"),
            "rate_5g_mbps": n(4804, "4x4 802.11ax PHY rate at 160 MHz; part of the official 5.38 Gbps aggregate"),
            "total_spatial_streams": n(8, "Four spatial streams on each of the two serving radios"),
            "wireless_security": COMMON_SECURITY,
        },
    },
    "C9120AXI": {
        "url": URL_9120,
        "page": "Product specifications table",
        "title": "Cisco Catalyst 9120AX Series Access Points Data Sheet (updated 2023-11-29)",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": t(
                "Cisco Catalyst 9800, 3500, 5520, 8540 and virtual wireless controllers; Cisco DNA Center"
            ),
            "dimensions_mm": t("216 x 216 x 43 mm (W x L x H), excluding bracket"),
            "ethernet_interfaces": t("1 x 100/1000/2500 Multigigabit Ethernet; RJ-45 console; USB 2.0"),
            "max_power_consumption_w": n(25.5, "Maximum PoE consumption at full features with 802.3at"),
            "mimo_2g": t("4x4:4 MU-MIMO flexible radio"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C; above 40 °C both radios reduce from 4x4 to 2x2"),
            "power_method": t("802.3af PoE (reduced features); 802.3at PoE+ / Cisco UPOE for full features"),
            "rate_2g_mbps": n(574, "4x4 802.11ax PHY rate at 20 MHz; part of the official 5.38 Gbps aggregate"),
            "rate_5g_mbps": n(4804, "4x4 802.11ax PHY rate at 160 MHz; part of the official 5.38 Gbps aggregate"),
            "total_spatial_streams": n(8, "Four spatial streams on each of the two serving radios"),
            "wireless_security": COMMON_SECURITY,
        },
    },
    "C9124AXE": {
        "url": URL_9124,
        "page": "Product specifications table",
        "title": "Cisco Catalyst 9124AX Series Access Points Data Sheet (updated 2023-03-22)",
        "values": {
            "antenna_gain_dbi": t("Certified for external antennas up to 13 dBi on 2.4 GHz and 5 GHz"),
            "antenna_type": t("External antennas with Self-Identifiable Antenna support"),
            "centralized_management": t("Cisco Catalyst 9800 Series Wireless Controllers; Cisco DNA Center"),
            "dimensions_mm": t("259 x 233 x 81 mm (W x L x H), excluding bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500BASE-T uplink; 1 x 1G SFP; 1 x 10/100/1000BASE-T downlink with PoE output; "
                "RJ-45 console"
            ),
            "fast_roaming": t("IEEE 802.11r fast transition"),
            "ip_rating": t("IP66/IP67"),
            "mimo_2g": t("4x4:4 uplink/downlink MU-MIMO"),
            "operating_temperature_c": t("-40 to 65 °C without solar loading; -40 to 55 °C with solar loading"),
            "power_method": t("802.3af/at/bt PoE, Cisco UPOE, or 24-56 V DC input"),
            "rate_2g_mbps": n(574, "4x4 802.11ax PHY rate at 20 MHz; part of the official 5.38 Gbps aggregate"),
            "rate_5g_mbps": n(4804, "Aggregate of the two 2x2 5 GHz radios; part of the official 5.38 Gbps total"),
            "total_spatial_streams": n(8, "4x4:4 on 2.4 GHz plus two 2x2:2 radios on 5 GHz"),
            "wireless_security": t("WPA3-Enterprise 192, WPA3, WPA2, WPA, 802.1X, AES and TKIP"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Catalyst 9105/9115/9120/9124 AP specifications."
    products = PRODUCTS
    document_version = "Official Cisco data sheets; accessed 2026-10-16"
    brand_name = "Cisco"
