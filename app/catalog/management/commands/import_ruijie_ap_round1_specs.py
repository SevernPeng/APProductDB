from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
    u,
)


PRODUCTS = {
    "RG-AP110-L": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/wal-mount-access-point-series/ap110-l",
        "page": "Specifications and management sections",
        "title": "Ruijie RG-AP110-L official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz", "Single-band 2.4 GHz"),
            "rate_2g_mbps": n(300, "Maximum throughput: 300 Mbps"),
            "rate_5g_mbps": u("Single-band 2.4 GHz model; prior tri-band scrape was incorrect"),
            "rate_6g_mbps": u("Single-band 2.4 GHz model; prior tri-band scrape was incorrect"),
            "mimo_2g": t("2x2 MIMO"),
            "mimo_5g": u("Single-band 2.4 GHz model"),
            "mimo_6g": u("Single-band 2.4 GHz model"),
            "total_spatial_streams": n(2),
            "max_channel_width_mhz": u("Official page does not publish a maximum channel width"),
            "max_clients": n(32, "Maximum clients per AP: 32"),
            "max_ssids": n(8, "BSSID capacity: 8"),
            "ethernet_interfaces": t(
                "Front: 1 x 10/100 Mbps LAN; rear: 1 x 10/100 Mbps uplink"
            ),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(5, "Less than 5 W"),
            "dimensions_mm": t("86 x 85 x 34 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antenna, 2x2"),
            "antenna_gain_dbi": u(
                "The 3.5 dBi value on the comparison table belongs to RG-AP130(L), not RG-AP110-L"
            ),
            "centralized_management": t(
                "Ruijie Cloud or on-premises Ruijie hardware wireless controller"
            ),
            "wireless_security": t(
                "WPA (TKIP), WPA2 (AES), WPA-PSK, WEP 64/128-bit; web portal authentication"
            ),
            "mounting_options": t(
                "Standard 86-type faceplate; optional universal kit for US/EU junction boxes"
            ),
        },
    },
    "RG-AP180P-L": {
        "url": "https://www.ruijie.com/en-global/products/wireless/wall-plate-access-points/rg-ap180p-l",
        "page": "Hardware and software specifications",
        "title": "Ruijie RG-AP180P-L official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256, "Maximum associated clients: 256; recommended active devices: 120"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio, 32 total"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2.5GBASE-T uplink; 4 x 10/100/1000BASE-T downlink; Micro-USB console"
            ),
            "poe_output": t("LAN 1 provides 48 V / 10 W PoE output when sufficient input power is available"),
            "power_method": t("48 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(25),
            "dimensions_mm": t("86 x 170 x 43 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antennas: two 2.4 GHz and two 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 5 dBi"),
            "centralized_management": t("Ruijie Cloud, Eweb, or Ruijie wireless controller; Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 wireless roaming"),
            "wireless_security": t(
                "WEP; WPA/WPA2/WPA3 Personal and Enterprise; OWE; PSK, web, 802.1X and RADIUS authentication"
            ),
            "mounting_options": t("Wall or 86 mm/European/American-standard junction box mount"),
        },
    },
    "RG-AP840-L": {
        "url": "https://www.ruijie.com/en-global/products/wireless/indoor-access-points/rg-ap840-l",
        "page": "Hardware and software specifications",
        "title": "Ruijie RG-AP840-L official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(4804),
            "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("4x4 SU-MIMO and MU-MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "Maximum associated clients: 1024; recommended active devices: 150"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio, 32 total"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2.5G/5GBASE-T; 1 x 5GE SFP/RJ45 combo; "
                "1 x 10/100/1000BASE-T; RJ45 console; USB 3.0"
            ),
            "poe_output": t("LAN 2 provides 48 V / 12.95 W PoE output when powered by 802.3bt"),
            "power_method": t("54 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(40),
            "dimensions_mm": t("230 x 230 x 51 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antennas: two 2.4 GHz and four 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 6 dBi"),
            "centralized_management": t("Ruijie Cloud, Eweb, or Ruijie wireless controller; Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 wireless roaming"),
            "wireless_security": t(
                "WEP; WPA/WPA2/WPA3 Personal and Enterprise; OWE; PSK, web, 802.1X and RADIUS authentication"
            ),
            "mounting_options": t("Wall or ceiling mount"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-AP110-L, RG-AP180P-L, and RG-AP840-L specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie product pages; accessed 2026-10-19"
    brand_name = "Ruijie"
