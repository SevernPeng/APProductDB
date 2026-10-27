from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


AP210_VALUES = {
    "supported_bands": t("2.4 GHz"),
    "rate_2g_mbps": n(300),
    "mimo_2g": t("2x2 MIMO"),
    "total_spatial_streams": n(2),
    "max_channel_width_mhz": n(40, "802.11n 2x2 maximum rate is specified as 300 Mbps"),
    "max_clients": n(128),
    "max_ssids": n(16),
    "ethernet_interfaces": t("1 x 10/100BASE-T Ethernet PoE uplink port"),
    "power_method": t("12 V DC or IEEE 802.3af PoE"),
    "max_power_consumption_w": n(7.5, "Less than 7.5 W"),
    "dimensions_mm": t("175 x 175 x 25.8 mm"),
    "operating_temperature_c": t("-10 to 50 °C"),
    "operating_humidity": t("5% to 95% RH, non-condensing"),
    "antenna_type": t("Built-in omnidirectional antennas"),
    "antenna_gain_dbi": t("2.4 GHz: 3 dBi"),
    "ip_rating": t("IP41"),
    "centralized_management": t("Ruijie Cloud, Cloud AC, hardware wireless controller, web, or Fat/Fit modes"),
    "wireless_security": t("WEP; WPA/WPA2 and WPA-PSK; PSK, web, 802.1X, PEAP and RADIUS"),
    "mounting_options": t("Wall or ceiling"),
}


PRODUCTS = {
    "RG-AP210": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/indoor-access-point-series/ap210-l",
        "page": "Official RG-AP210-L product specifications",
        "title": "Ruijie RG-AP210-L official specifications (RG-AP210 database alias)",
        "values": AP210_VALUES,
    },
    "RG-AP210-L": {
        "url": "https://www.ruijie.com/vi-vn/products/wireless/indoor-access-point-series/ap210-l",
        "page": "Official product specifications and current linked datasheet",
        "title": "Ruijie RG-AP210-L official product specifications",
        "values": AP210_VALUES,
    },
    "RG-AP680-L": {
        "url": "https://www.ruijie.com/it-it/products/wireless/outdoor-access-points/rg-ap680-l",
        "page": "Current hardware/software specifications",
        "title": "Ruijie RG-AP680-L official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "Maximum associated clients; recommended maximum active devices: 120"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x Gigabit Ethernet PoE port; 1 x 1GE SFP port; RJ45 console"),
            "power_method": t("48 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(12.95),
            "dimensions_mm": t("251 x 168 x 64 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
            "operating_humidity": t("0% to 100% RH, non-condensing"),
            "antenna_type": t("Built-in high-power omnidirectional antennas; integrated Bluetooth antenna"),
            "antenna_gain_dbi": t("2.4 GHz: 3.5 dBi; 5 GHz: 5.5 dBi; Bluetooth: 5 dBi"),
            "ip_rating": t("IP68"),
            "lightning_protection_kv": t("6 kV"),
            "wireless_range": t("Up to 300 m radius in Ruijie field testing; actual range varies by environment and client"),
            "centralized_management": t("Ruijie Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 wireless roaming"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3 Personal and Enterprise; OWE; PSK, web, 802.1X, RADIUS, SMS and MAB"),
            "mounting_options": t("Pole or ceiling"),
        },
    },
    "RG-AP820-L": {
        "url": "https://www.ruijie.com/en-global/products/wireless/indoor-access-points/rg-ap820-l-v3",
        "page": "Current RG-AP820-L(V3) hardware/software specifications",
        "title": "Ruijie RG-AP820-L(V3) official product specifications (current version)",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2 MIMO"),
            "mimo_5g": t("2x2 MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256, "Maximum associated clients; recommended maximum active devices: 120"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x Gigabit Ethernet PoE port; 1 x 2.5GE SFP port compatible with 1GE; RJ45 console"),
            "power_method": t("48 V DC or IEEE 802.3af PoE"),
            "max_power_consumption_w": n(12.95),
            "dimensions_mm": t("220 x 220 x 49 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("0% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antennas: two 2.4 GHz and two 5 GHz; onboard Bluetooth antenna"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 5 dBi; Bluetooth: 2.4 dBi"),
            "ip_rating": t("IP41"),
            "centralized_management": t("Ruijie Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2/Layer 3 roaming and IEEE 802.11k/v/r seamless roaming"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3 Personal and Enterprise; OWE; PSK, web, 802.1X, RADIUS, SMS and MAB"),
            "mounting_options": t("Wall or ceiling"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-AP210-L aliases, RG-AP680-L, and current RG-AP820-L(V3) specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie pages/datasheets; accessed 2026-10-19"
    brand_name = "Ruijie"
