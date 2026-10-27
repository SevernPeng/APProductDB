from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL_9105 = "https://www.cisco.com/c/en/us/products/collateral/wireless/catalyst-9100ax-access-points/datasheet-c78-744062.html"
URL_9171 = "https://www.cisco.com/site/us/en/products/collateral/networking/wireless/access-points/wireless-9171-series-acc-point-ds.html"
URL_9172 = "https://www.cisco.com/site/us/en/products/collateral/networking/wireless/access-points/wireless-9172-series-access-points-ds.html"
URL_9174 = "https://www.cisco.com/site/us/en/products/collateral/networking/wireless/access-points/wireless-9174-series-access-points-ds.html"
URL_9176 = "https://www.cisco.com/site/us/en/products/collateral/networking/wireless/access-points/wireless-9176-series-access-points-ds.html"
URL_9178 = "https://www.cisco.com/site/us/en/products/collateral/networking/wireless/access-points/wireless-9178-series-access-points-ds.html"


WIFI7_SECURITY = t("WPA3 and WPA2/WPA3 support; 802.1X enterprise authentication")
WIFI7_MANAGEMENT = t(
    "Cisco Catalyst/Cisco Wireless 9800 Series controllers, Catalyst 9000 Embedded Wireless Controller, "
    "or Cisco Meraki cloud management"
)


PRODUCTS = {
    "CW9105AXW": {
        "url": URL_9105,
        "page": "Product specifications table, updated 2022-11-03",
        "title": "Cisco Catalyst 9105 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 5 dBi peak gain"),
            "antenna_type": t("Internal directional antennas"),
            "centralized_management": t(
                "Cisco Catalyst wireless controllers, including Catalyst 9800; Cisco DNA Center"
            ),
            "dimensions_mm": t("90 x 160 x 32.66 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500BASE-T uplink; 3 x 10/100/1000BASE-T downlinks; "
                "RJ-45 console; USB 2.0; passthrough port"
            ),
            "max_channel_width_mhz": n(80, "802.11ax supports 20, 40 and 80 MHz channels"),
            "mimo_2g": t("2x2:2 uplink/downlink MU-MIMO"),
            "mimo_5g": t("2x2:2 uplink/downlink MU-MIMO"),
            "operating_temperature_c": t(
                "0 to 50 °C; above 40 °C the 2.4 GHz radio reduces to 1x1 and USB/LAN1 PSE are disabled"
            ),
            "poe_output": t("LAN1 provides up to 10.5 W PSE output when enabled with 802.3at power"),
            "power_method": t(
                "802.3af PoE; 802.3at PoE+ / Cisco UPOE; AIR-PWRINJ5 or AIR-PWRINJ6 injector"
            ),
            "rate_2g_mbps": n(287, "2x2 802.11ax PHY rate at 20 MHz; part of the official 1.488 Gbps aggregate"),
            "rate_5g_mbps": n(1201, "2x2 802.11ax PHY rate at 80 MHz; part of the official 1.488 Gbps aggregate"),
            "total_spatial_streams": n(4, "Two spatial streams on each of the two serving radios"),
            "wireless_security": t("WPA3, WPA2, WPA, 802.1X and AES; enterprise EAP methods"),
        },
    },
    "CW9171I": {
        "url": URL_9171,
        "page": "Product specifications table, updated 2026-04-06",
        "title": "Cisco Wireless 9171 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5.5 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("200 x 200 x 53 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500 Multigigabit Ethernet uplink; RJ-45 console; USB 2.0 at 4.5 W; 54 V DC jack"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(30, "Official maximum power requirement"),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO; 5/6 GHz radio is selectable"),
            "mimo_6g": t("2x2:2 MU-MIMO; 5/6 GHz radio is selectable"),
            "operating_temperature_c": t("0 to 50 °C; radio operation is derated from 40 to 50 °C"),
            "power_method": t("802.3at PoE+ for full operation; 802.3af reduced mode; optional 54 V DC input"),
            "rate_2g_mbps": n(344, "2x2 Wi-Fi 7 PHY rate at 20 MHz, derived from the official 6.12 Gbps aggregate"),
            "rate_5g_mbps": n(2882, "2x2 Wi-Fi 7 PHY rate at 160 MHz when the selectable radio uses 5 GHz"),
            "rate_6g_mbps": n(5765, "2x2 Wi-Fi 7 PHY rate at 320 MHz when the selectable radio uses 6 GHz"),
            "total_spatial_streams": n(4, "Two spatial streams on each of two concurrent serving radios"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
    "CW9172I": {
        "url": URL_9172,
        "page": "Product specifications table, updated 2026-09-15",
        "title": "Cisco Wireless 9172 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5.5 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("200 x 200 x 53 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500 Multigigabit Ethernet uplink; RJ-45 console; USB 2.0 at 4.5 W"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(32, "Maximum PoE requirement in full tri-radio mode with USB enabled"),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 tri-radio mode or 4x4:4 dual-radio mode"),
            "mimo_6g": t("2x2:2 MU-MIMO in tri-radio mode"),
            "operating_temperature_c": t("0 to 50 °C; radio operation is derated from 40 to 50 °C"),
            "power_method": t("802.3bt Class 5/UPOE; 802.3at PoE+; 802.3af reduced mode"),
            "rate_2g_mbps": n(344, "2x2 Wi-Fi 7 PHY rate at 20 MHz; part of official aggregate rates"),
            "rate_5g_mbps": n(5765, "Maximum 4x4 Wi-Fi 7 PHY rate at 160 MHz in dual-radio mode"),
            "rate_6g_mbps": n(5765, "2x2 Wi-Fi 7 PHY rate at 320 MHz in tri-radio mode"),
            "total_spatial_streams": n(6, "Six total serving spatial streams in either published radio mode"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
    "CW9172H": {
        "url": URL_9172,
        "page": "Product specifications table, updated 2026-09-15",
        "title": "Cisco Wireless 9172 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 7 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("130 x 180 x 26 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500 Multigigabit Ethernet uplink; 3 x 100/1000 Ethernet LAN ports; "
                "RJ-45 console; passthrough port"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(41, "Maximum PoE requirement with tri-radio operation and PoE output enabled"),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "mimo_6g": t("2x2:2 MU-MIMO"),
            "operating_temperature_c": t("0 to 40 °C; published performance derating extends operation to 50 °C"),
            "poe_output": t("One LAN port provides up to 15.4 W PoE output with 802.3bt Class 5 input"),
            "power_method": t("802.3bt Class 5/UPOE; 802.3at PoE+; 802.3af reduced mode"),
            "rate_2g_mbps": n(344, "2x2 Wi-Fi 7 PHY rate at 20 MHz; part of the official 9 Gbps aggregate"),
            "rate_5g_mbps": n(2882, "2x2 Wi-Fi 7 PHY rate at 160 MHz; part of the official 9 Gbps aggregate"),
            "rate_6g_mbps": n(5765, "2x2 Wi-Fi 7 PHY rate at 320 MHz; part of the official 9 Gbps aggregate"),
            "total_spatial_streams": n(6, "Two spatial streams on each of three serving radios"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
    "CW9174I": {
        "url": URL_9174,
        "page": "Product specifications table, updated 2026-09-15",
        "title": "Cisco Wireless 9174 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 5 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("226 x 226 x 49 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500/5000 Multigigabit Ethernet; RJ-45 console; USB 2.0 at 9 W; 54 V DC jack"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(37, "Maximum PoE requirement in full 10-spatial-stream tri-band mode"),
            "mimo_2g": t("2x2:2 tri-band mode or 4x4:4 dual-band mode"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "mimo_6g": t("4x4:4 MU-MIMO in tri-band mode"),
            "operating_temperature_c": t("0 to 50 °C"),
            "power_method": t("802.3bt Class 5/UPOE or 54 V DC; 802.3at PoE+ reduced link/USB; 802.3af staging mode"),
            "rate_2g_mbps": n(344, "2x2 Wi-Fi 7 PHY rate at 20 MHz in tri-band mode"),
            "rate_5g_mbps": n(5765, "4x4 Wi-Fi 7 PHY rate at 160 MHz"),
            "rate_6g_mbps": n(11529, "4x4 Wi-Fi 7 PHY rate at 320 MHz; official aggregate is about 17.5 Gbps"),
            "total_spatial_streams": n(10, "2x2:2 on 2.4 GHz plus 4x4:4 on 5 GHz and 6 GHz"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
    "CW9176I": {
        "url": URL_9176,
        "page": "Product specifications table, updated 2026-04-09",
        "title": "Cisco Wireless 9176 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 5 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("240 x 240 x 51 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2500/5000/10000 Multigigabit Ethernet; RJ-45 console; USB 2.0 at 9 W"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(39, "Maximum PoE requirement with full 4x4 radios and USB enabled"),
            "mimo_2g": t("4x4:4 MU-MIMO on selectable 2.4/5 GHz radio"),
            "mimo_5g": t("4x4:4 MU-MIMO; second selectable 2.4/5 GHz radio can also serve 5 GHz"),
            "mimo_6g": t("4x4:4 MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C"),
            "power_method": t("802.3bt Class 5/UPOE or CW-INJ-8; 802.3at PoE+ reduced mode; 802.3af staging only"),
            "rate_2g_mbps": n(688, "4x4 Wi-Fi 7 PHY rate at 20 MHz in tri-band mode"),
            "rate_5g_mbps": n(5765, "4x4 Wi-Fi 7 PHY rate at 160 MHz for one 5 GHz radio"),
            "rate_6g_mbps": n(11529, "4x4 Wi-Fi 7 PHY rate at 320 MHz; official tri-band aggregate is 18 Gbps"),
            "total_spatial_streams": n(12, "Four spatial streams on each of three concurrent serving radios"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
    "CW9178I": {
        "url": URL_9178,
        "page": "Product specifications table, updated 2026-08-10",
        "title": "Cisco Wireless 9178 Series Access Points Data Sheet",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi; 6 GHz: 6 dBi peak gain"),
            "antenna_type": t("Internal omnidirectional antennas"),
            "centralized_management": WIFI7_MANAGEMENT,
            "dimensions_mm": t("251 x 251 x 51 mm (W x L x H), excluding mounting bracket"),
            "ethernet_interfaces": t(
                "2 x 100/1000/2500/5000/10000 Multigigabit Ethernet; RJ-45 console; USB 2.0 at 9 W"
            ),
            "max_channel_width_mhz": n(320, "Up to 320 MHz on 6 GHz; up to 160 MHz on 5 GHz"),
            "max_power_consumption_w": n(47, "Maximum PoE requirement in full quad-radio mode with USB enabled"),
            "mimo_2g": t("4x4:4 MU-MIMO"),
            "mimo_5g": t("Two concurrent 4x4:4 MU-MIMO radios in quad-radio mode"),
            "mimo_6g": t("4x4:4 MU-MIMO"),
            "operating_temperature_c": t("0 to 50 °C; above 40 °C radios reduce from 4x4 to 2x2"),
            "power_method": t("802.3bt Class 6/UPOE or CW-INJ-8; 802.3at PoE+ reduced mode; 802.3af staging only"),
            "rate_2g_mbps": n(688, "4x4 Wi-Fi 7 PHY rate at 20 MHz in quad-radio mode"),
            "rate_5g_mbps": n(11529, "Aggregate of two 4x4 Wi-Fi 7 160 MHz 5 GHz radios in quad-radio mode"),
            "rate_6g_mbps": n(11529, "4x4 Wi-Fi 7 PHY rate at 320 MHz; official quad-radio aggregate is 24 Gbps"),
            "total_spatial_streams": n(16, "Four spatial streams on each of four concurrent serving radios"),
            "wireless_security": WIFI7_SECURITY,
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco CW9105AXW and CW9171/9172/9174/9176/9178 AP specifications."
    products = PRODUCTS
    document_version = "Latest official Cisco data sheets; accessed 2026-10-16"
    brand_name = "Cisco"
