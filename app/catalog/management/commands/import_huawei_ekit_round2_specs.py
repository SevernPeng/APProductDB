from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "eKit AP361": {
        "url": "https://e.huawei.com/kz/material/enterprise/4066e75a6d3a470f87517b6eaa8c6102",
        "page": "Official datasheet and official eKit product portfolio",
        "title": "Huawei eKitEngine AP361 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(1200),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(80),
            "max_clients": n(128),
            "max_ssids": n(6, "Per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE-in"),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(8.8),
            "dimensions_mm": t("Ø180 x 35 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mounting_options": t("Wall, ceiling, or T-rail"),
            "centralized_management": t(
                "EasyWeb, Huawei WAC, HUAWEI eKit App, or SNC; Fat, Fit, and cloud management modes"
            ),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming"),
            "wireless_security": t(
                "WEP; WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
                "WPA-WPA2 and WPA2-WPA3 mixed authentication"
            ),
        },
    },
    "eKit AP362": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/d59ee6b254e447148946d91e8e979574/M3T1A590N1110978119643799820/HUAWEI%20eKit%20SME%20NetWork%20Scenario-based%20Products%20Manual.pdf",
        "page": "Official eKit product portfolio and product datasheet",
        "title": "Huawei eKitEngine AP362 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(2400),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE-in"),
            "power_method": t("12 V DC or IEEE 802.3af PoE"),
            "max_power_consumption_w": n(11.2),
            "dimensions_mm": t("Ø180 x 35 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 4 dBi"),
            "mounting_options": t("Wall, ceiling, or T-rail"),
            "centralized_management": t(
                "EasyWeb, Huawei WAC, HUAWEI eKit App, or SNC; Fat, Fit, and cloud management modes"
            ),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming"),
            "wireless_security": t(
                "WEP; WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
                "WPA-WPA2 and WPA2-WPA3 mixed authentication"
            ),
        },
    },
    "eKit AP572": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/9480040753bf4c83900c06d4d32c7e84/M3T1A590N1197650865257734156/HUAWEI%20eKitEngine%20AP572%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet",
        "title": "Huawei eKitEngine AP572 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(690),
            "rate_5g_mbps": n(5760),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("4x4:4 MU-MIMO"),
            "total_spatial_streams": n(6),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024),
            "max_ssids": n(10, "Per radio"),
            "ethernet_interfaces": t(
                "1 x 100M/1G/2.5GE PoE-in; 1 x 10/100/1000BASE-T; 1 x USB"
            ),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(14.8, "Excluding USB"),
            "dimensions_mm": t("Ø220 x 45 mm"),
            "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mounting_options": t("Wall, ceiling, T-rail, or junction box"),
            "centralized_management": t(
                "EasyWeb, Huawei WAC, HUAWEI eKit App, or SNC; Fit, Fat, and cloud management modes"
            ),
            "mesh_support": b(True, "Mesh backhaul listed in the official datasheet"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
                "WPA-WPA2 and WPA2-WPA3 mixed authentication; 802.1X, MAC, and Portal authentication"
            ),
        },
    },
    "eKit AP761": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/d5af8471cd2041e4add8b11e27336eee/M3T1A590N1169748915087012100/Huawei%20eKitEngine%20AP761%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet",
        "title": "Huawei eKitEngine AP761 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(1200),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(80),
            "max_clients": n(1024, "512 per radio"),
            "max_ssids": n(16, "Per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE-in; 1 x SFP optical port"),
            "power_method": t("IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(17.7),
            "dimensions_mm": t("200 x 200 x 69 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
            "ip_rating": t("IP68"),
            "lightning_protection_kv": t("6 kA surge protection for Ethernet ports"),
            "antenna_type": t("Built-in directional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 11 dBi"),
            "centralized_management": t("Huawei WAC in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA/WPA2 and WPA2/WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; IPsec/DTLS"
            ),
        },
    },
    "eKit AP771": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/361bd75eea574df49b3f39c9b364f02b/M3T1A590N1187274761666556192/Huawei%20eKitEngine%20AP771%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet",
        "title": "Huawei eKitEngine AP771 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(690),
            "rate_5g_mbps": n(2880),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256),
            "max_ssids": n(10, "Per radio"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5GE PoE-in"),
            "power_method": t("IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(18.8),
            "dimensions_mm": t("270 x 196 x 51 mm"),
            "operating_temperature_c": t("-30 to 60 °C"),
            "ip_rating": t("IP65"),
            "lightning_protection_kv": t("6 kA surge protection for Ethernet ports"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 7 dBi"),
            "mounting_options": t("Pole or wall"),
            "wireless_range": t("130 m optimal experience radius"),
            "centralized_management": t("Huawei WAC in Fit mode; Fat mode; Huawei SME Network cloud platform"),
            "mesh_support": b(True, "Mesh backhaul listed in the official datasheet"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; PMF; DTLS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei eKit AP361, AP362, AP572, AP761, and AP771 specifications."
    products = PRODUCTS
    document_version = "Current official Huawei eKit datasheets, product pages, and portfolio; accessed 2026-10-19"
    brand_name = "Huawei"
