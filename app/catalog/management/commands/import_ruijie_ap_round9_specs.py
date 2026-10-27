from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
    u,
)


PRODUCTS = {
    "RG-SAP825-SP": {
        "url": "https://www.ruijie.com/en-global/products/wireless/scenario-based-wireless/rg-sap825-sp",
        "page": "Official hardware and software specifications",
        "title": "Ruijie RG-SAP825-SP official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(2402),
            "mimo_2g": t("2x2 uplink/downlink MU-MIMO"),
            "mimo_5g": t("2x2 uplink/downlink MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256, "Up to 128 associated STAs per radio; practical maximum per device: 128"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x Gigabit Ethernet plus 1 x 2.5GE SFP/RJ45 combo (shared); RJ45 console; Bluetooth 5.1"),
            "power_method": t("48 V DC or IEEE 802.3af PoE"),
            "max_power_consumption_w": n(12.95),
            "dimensions_mm": t("220 x 220 x 49 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "operating_humidity": t("0% to 95% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional smart antennas for 2.4 GHz and 5 GHz; built-in Bluetooth antenna"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 5.7 dBi; Bluetooth: 2.4 dBi"),
            "centralized_management": t("Eweb, Ruijie wireless controller, Ruijie Cloud, WIS, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2/Layer 3 roaming; IEEE 802.11k/v/r"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3; PSK, web, QR-code, SMS, MAB and RADIUS authentication"),
            "wireless_range": u("The previous value was an altitude range, not a wireless coverage range; the official page does not publish a coverage distance"),
            "mounting_options": t("Wall or ceiling"),
        },
    },
    "RG-AP850-AR": {
        "url": "https://www.ruijie.com/es-es/products/wireless/indoor-access-points/rg-ap850-ar-v3",
        "page": "Current RG-AP850-AR(V3) hardware and software specifications",
        "title": "Ruijie RG-AP850-AR(V3) official product specifications (current version)",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(4804, "Two 5 GHz service radios, each up to 2402 Mbps; AI radio is scanning-only"),
            "mimo_2g": t("2x2 uplink/downlink MU-MIMO"),
            "mimo_5g": t("Two 2x2 uplink/downlink MU-MIMO service radios"),
            "total_spatial_streams": n(8, "Six service-radio streams plus two streams on the scanning-only AI radio"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1552),
            "max_ssids": n(48, "Up to 16 BSSIDs per service radio"),
            "ethernet_interfaces": t("1 x 100/1000/2.5G/5G RJ45; 1 x 5GE SFP/RJ45 combo (shared); 1 x Gigabit RJ45; RJ45 console; USB 3.0; Bluetooth 5.1"),
            "power_method": t("48 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(40),
            "dimensions_mm": t("230 x 230 x 51 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "centralized_management": t("WIS Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2/Layer 3 roaming with AI-radio client steering; under 30 ms average roaming latency in Ruijie testing"),
            "wireless_security": t("WEP; WPA/WPA2/WPA3 Personal and Enterprise; PSK, web, QR-code, SMS, MAB and RADIUS authentication"),
            "wireless_range": u("The previous value was an altitude range, not a wireless coverage range; the official page does not publish a coverage distance"),
            "mounting_options": t("Wall or ceiling"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-SAP825-SP and current RG-AP850-AR(V3) specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie product pages; accessed 2026-10-19"
    brand_name = "Ruijie"
