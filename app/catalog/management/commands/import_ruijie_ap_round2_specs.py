from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "RG-AP840-I": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/indoor-access-point-series/rg-ap840-i",
        "page": "Official specifications and order information",
        "title": "Ruijie RG-AP840-I official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(400),
            "rate_5g_mbps": n(4800),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("4x4:4 MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(160, "802.11ax HT160 is listed in receiver specifications"),
            "max_clients": n(1024, "Maximum 1024 clients; recommended 64"),
            "max_ssids": n(32),
            "ethernet_interfaces": t(
                "3 x 10/100/1000 Mbps Ethernet (LAN1 PoE-in; LAN3 LAN/IoT expansion with passive PoE-out); "
                "1 x console; 1 x USB 2.0"
            ),
            "poe_output": t("LAN3 provides passive PoE output for IoT expansion; disabled under 802.3af input"),
            "power_method": t("48 V DC, IEEE 802.3at PoE+, or restricted IEEE 802.3af PoE"),
            "max_power_consumption_w": n(25.4, "Less than 25.4 W"),
            "dimensions_mm": t("220 x 220 x 48.85 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Integrated antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 3 dBi"),
            "centralized_management": t(
                "Ruijie WS controller, RG-MACC-Base, Ruijie Cloud, or standalone Fat mode"
            ),
            "wireless_security": t("WEP 64/128-bit; WPA/WPA2/WPA3; WPA-PSK; web and 802.1X authentication"),
            "mounting_options": t("Ceiling or wall mount"),
        },
    },
    "RG-AP9861-R": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/indoor-access-points/ap9861r",
        "page": "Current hardware/software specifications and order information",
        "title": "Ruijie RG-AP9861-R official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(1377, "Wi-Fi 7 Radio 1 peak: 1.377 Gbps"),
            "rate_5g_mbps": n(11530, "Two 5 GHz service radios at 5.765 Gbps each"),
            "rate_6g_mbps": n(11529, "6 GHz service radio peak: 11.529 Gbps"),
            "mimo_2g": t("4x4 MU-MIMO service radio; 2x2 AI scanning radio also supports 2.4/5 GHz"),
            "mimo_5g": t("Two 4x4 MU-MIMO service radios; 2x2 AI scanning radio"),
            "mimo_6g": t("4x4 MU-MIMO"),
            "total_spatial_streams": n(18, "16 service-radio spatial streams plus 2 AI-radio spatial streams"),
            "max_channel_width_mhz": n(320),
            "max_clients": n(2048, "Up to 512 associated STAs per service radio; 2,048 total"),
            "max_ssids": n(64, "Up to 16 BSSIDs per service radio; 64 total"),
            "ethernet_interfaces": t(
                "1 x 10GBASE-T PoE-in; 1 x 10GBASE-T multiplexed with 1 x 10GE SFP+; "
                "1 x Gigabit Ethernet; RJ45 console; USB 3.0; Bluetooth 5.3"
            ),
            "poe_output": t("Gigabit LAN supplies 48 V / 12.95 W and USB supplies 5 V / 5 W under DC or 802.3bt"),
            "power_method": t("54 V DC or IEEE 802.3at/bt PoE"),
            "max_power_consumption_w": n(60),
            "dimensions_mm": t("245 x 245 x 67 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t(
                "Built-in omnidirectional smart antennas: four 2.4 GHz, eight 5 GHz, four 6 GHz, "
                "and two 2.4/5 GHz AI-radio antennas"
            ),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 3 dBi; 6 GHz: 3 dBi; AI radio: 3 dBi"),
            "centralized_management": t("WIS Cloud, Ruijie wireless controller, Eweb, or Fat/Fit/Cloud mode"),
            "fast_roaming": t("Layer 2 and Layer 3 roaming; AI radio supports seamless roaming optimization"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3; PSK, web, 802.1X, RADIUS, QR-code, SMS and MAB authentication"),
            "mounting_options": t("Wall or ceiling mount"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-AP840-I and RG-AP9861-R specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie product pages; accessed 2026-10-19"
    brand_name = "Ruijie"
