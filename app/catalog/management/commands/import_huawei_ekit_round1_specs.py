from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "eKit AP266": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/e54ac3a76f614189835e8e99aa514939/M3T1A590N1051921978522906890/Huawei%20eKitEngine%20AP266%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "Official product datasheet",
        "title": "Huawei eKitEngine AP266 official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(2400),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(128),
            "max_ssids": n(16),
            "ethernet_interfaces": t(
                "1 x GE uplink PoE-in; 4 x GE downlink (one supports PoE out)"
            ),
            "poe_output": t("One GE downlink port supports PoE out"),
            "power_method": t("IEEE 802.3at PoE"),
            "max_power_consumption_w": n(9.4, "Excluding PoE output power"),
            "dimensions_mm": t("86 x 160 x 38 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 4 dBi"),
            "mounting_options": t("Desktop, wall, ceiling, or junction box"),
            "centralized_management": t(
                "EasyWeb or Huawei WAC for local management; HUAWEI eKit App and SNC for remote management"
            ),
            "wireless_security": t(
                "WEP; WPA/WPA2-PSK; WPA3-SAE; WPA/WPA2-PPSK; "
                "WPA/WPA2/WPA3-802.1X; PMF"
            ),
        },
    },
    "eKit AP271H-P": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/bdbf47a5aca54cae8d2e44d69b51b23a/M3T1A590N1263931343900192999/HUAWEI%20eKitEngine%20AP271H-P%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet",
        "title": "Huawei eKitEngine AP271H-P official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(688),
            "rate_5g_mbps": n(2882),
            "mimo_2g": t("2x2:2 MIMO"),
            "mimo_5g": t("2x2:2 MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_clients": n(256),
            "max_ssids": n(10, "Per radio"),
            "ethernet_interfaces": t(
                "1 x 100M/1G/2.5GE uplink PoE-in; 5 x 10M/100M/GE downlink; GE3 and GE4 support PoE output"
            ),
            "poe_output": t("Two GE downlink ports (GE3 and GE4) support PoE output"),
            "power_method": t("48 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(15.9),
            "dimensions_mm": t("185 x 86 x 45 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi; 5 GHz: 6 dBi"),
            "mounting_options": t("86 mm junction box, wall, or ceiling"),
            "wireless_range": t("18 m optimal experience radius"),
            "centralized_management": t(
                "EasyWeb or Huawei WAC for local management; HUAWEI eKit App and SNC for remote management"
            ),
            "mesh_support": b(True, "Mesh backhaul listed in the official datasheet"),
            "wireless_security": t(
                "WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
                "WPA-WPA2 and WPA2-WPA3 mixed authentication; 802.1X, MAC, and Portal authentication"
            ),
        },
    },
    "eKit AP362E": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/4f22e1e4add9469691db144b30a0a508/M3T1A590N1187441795617796352/HUAWEI%20eKitEngine%20AP362E%20Wireless%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet",
        "title": "Huawei eKitEngine AP362E official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(575),
            "rate_5g_mbps": n(2400),
            "mimo_2g": t("2x2:2 MU-MIMO"),
            "mimo_5g": t("2x2:2 MU-MIMO"),
            "total_spatial_streams": n(4),
            "max_channel_width_mhz": n(160),
            "max_ssids": n(16),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE-in"),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(9.4),
            "dimensions_mm": t("Ø180 x 35 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "ip_rating": t("IP41"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mounting_options": t("Wall, ceiling, or T-rail"),
            "centralized_management": t(
                "EasyWeb, Huawei WAC, HUAWEI eKit App, or SNC; Fat, Fit, and cloud management modes"
            ),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming"),
            "wireless_security": t(
                "WEP; WPA/WPA2-PSK; WPA3-SAE; WPA/WPA2-PPSK; "
                "WPA/WPA2/WPA3-802.1X; PMF; DTLS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei eKit AP266, AP271H-P, and AP362E specifications."
    products = PRODUCTS
    document_version = "Current official Huawei eKit datasheets and product pages; accessed 2026-10-19"
    brand_name = "Huawei"
