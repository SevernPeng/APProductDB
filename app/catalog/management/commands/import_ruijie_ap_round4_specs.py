from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "RG-AP180": {
        "url": "https://www.ruijie.com/en-global/products/wireless/wall-plate-access-points/rg-ap180",
        "page": "Current hardware/software specifications",
        "title": "Ruijie RG-AP180 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1201),
            "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Maximum associated clients: 256; recommended active devices: 120"),
            "max_ssids": n(16, "Up to 8 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x Gigabit PoE uplink; 4 x Gigabit downlink; Micro-USB console"),
            "power_method": t("12 V DC or IEEE 802.3af PoE"),
            "max_power_consumption_w": n(10),
            "dimensions_mm": t("86 x 116 x 19 mm in-wall; 86 x 116 x 24 mm above-wall"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in intelligent antennas: two 2.4 GHz and two 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 2.5 dBi; 5 GHz: 5.5 dBi"),
            "centralized_management": t("Ruijie Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 wireless roaming"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3 Personal and Enterprise; OWE; PSK, web, 802.1X and RADIUS"),
            "mounting_options": t("Wall or 86 mm/European junction box; optional US-standard bracket"),
        },
    },
    "RG-AP180-I": {
        "url": "https://www.ruijie.com/en-global/products/wireless/wall-plate-access-points/rg-ap180-i",
        "page": "Current hardware/software specifications",
        "title": "Ruijie RG-AP180-I official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2 uplink/downlink MU-MIMO"),
            "mimo_5g": t("2x2 uplink/downlink MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256, "Up to 128 associated STAs per radio; practical maximum 128 per device"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x 2.5GBASE-T PoE uplink; 4 x Gigabit downlink; Micro-USB console; Bluetooth 5.1"),
            "poe_output": t("LAN 1 supplies 48 V / 10 W when powered by 802.3at or DC"),
            "power_method": t("48 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(25),
            "dimensions_mm": t("86 x 170 x 43 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "operating_humidity": t("5% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antennas: two 2.4 GHz and two 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 5.2 dBi; 5 GHz: 6 dBi"),
            "centralized_management": t("WIS Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 wireless roaming"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3 Personal and Enterprise; PSK, UPSK, web, RADIUS, SMS and MAB"),
            "mounting_options": t("Wall or 86 mm/American/European-standard junction box"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-AP180 and RG-AP180-I specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie product pages; accessed 2026-10-19"
    brand_name = "Ruijie"
