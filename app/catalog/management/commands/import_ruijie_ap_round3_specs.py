from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
    u,
)


CD_URL = "https://www.ruijie.com/vi-vn/products/wireless/cloud-managed-ap/ap680cd/"


def cd_values():
    return {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(574),
        "rate_5g_mbps": n(1200, "1.2 Gbps per 5 GHz radio; dual-5 GHz mode totals 2.4 Gbps"),
        "mimo_2g": t("2x2 MU-MIMO"),
        "mimo_5g": t("2x2 MU-MIMO"),
        "total_spatial_streams": n(4),
        "max_channel_width_mhz": n(80),
        "max_clients": n(1024, "Recommended maximum active devices: 120; maximum associated clients: 1024"),
        "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
        "ethernet_interfaces": t("1 x 10/100/1000BASE-T PoE uplink; 1 x 1G SFP; 1 x console"),
        "power_method": t("44-57 V DC or IEEE 802.3af/at PoE"),
        "max_power_consumption_w": n(12.95, "Less than 12.95 W"),
        "dimensions_mm": t("251 x 168 x 64 mm"),
        "operating_temperature_c": t("-40 to 65 °C"),
        "operating_humidity": t("0% to 100% RH, non-condensing"),
        "antenna_type": t("Built-in directional antenna, 60° beamwidth"),
        "antenna_gain_dbi": t("2.4/5 GHz: 9 dBi"),
        "centralized_management": t("Ruijie Cloud, RG-MACC, Ruijie WS controller, or standalone Fat mode"),
        "mesh_support": b(True, "Multi-hop and point-to-multipoint wireless bridging supported"),
        "fast_roaming": t("Seamless roaming with Ruijie wireless controller"),
        "wireless_security": t("WEP 64/128-bit; WPA/WPA2; TKIP/AES; PSK, web, RADIUS, SMS and MAB authentication"),
        "wireless_range": u("The previous value was an altitude range, not a wireless coverage range; the official page does not publish a coverage distance"),
        "ip_rating": t("IP68"),
        "lightning_protection_kv": t("±9 kV common-mode surge protection"),
        "mounting_options": t("Wall or pole mount"),
    }


PRODUCTS = {
    "RG-AP680(CD)": {
        "url": CD_URL,
        "page": "Current hardware/software specifications",
        "title": "Ruijie RG-AP680(CD) official product specifications",
        "values": cd_values(),
    },
    "RG-AP680-CD": {
        "url": CD_URL,
        "page": "Current hardware/software specifications; database alias of RG-AP680(CD)",
        "title": "Ruijie RG-AP680(CD) official product specifications",
        "values": cd_values(),
    },
    "RG-AP680-IO": {
        "url": "https://www.ruijie.com/de-de/products/wireless/outdoor-access-points/rg-ap680-io",
        "page": "Current hardware/software specifications",
        "title": "Ruijie RG-AP680-IO official product specifications",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1147),
            "rate_5g_mbps": n(4804),
            "mimo_2g": t("4x4 uplink/downlink MU-MIMO"),
            "mimo_5g": t("4x4 uplink/downlink MU-MIMO"),
            "total_spatial_streams": n(8),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "Up to 512 associated STAs per radio; practical maximum 250 per device"),
            "max_ssids": n(32, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t(
                "1 x 100/1000/2.5G/5GBASE-T; 1 x 100/1000BASE-T; "
                "1 x 10GE optical port (1GE/2.5GE compatible); RJ45 console; Bluetooth 5.1"
            ),
            "poe_output": t("LAN 2 provides external-device power under 802.3bt input"),
            "power_method": t("DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(40),
            "dimensions_mm": t("300 x 300 x 94 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
            "operating_humidity": t("0% to 100% RH, non-condensing"),
            "antenna_type": t("Built-in omnidirectional antennas: four 2.4 GHz and four 5 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 6 dBi; 5 GHz: 5 dBi"),
            "centralized_management": t("WIS Cloud, Eweb, Ruijie wireless controller, or Fat/Fit/Cloud modes"),
            "fast_roaming": t("Layer 2 and Layer 3 roaming"),
            "wireless_security": t(
                "WEP; WPA/WPA2/WPA3 Personal and Enterprise; PSK, UPSK, web, RADIUS, SMS and MAB authentication"
            ),
            "ip_rating": t("IP68"),
            "lightning_protection_kv": t("6 kV lightning protection"),
            "mounting_options": t("Wall or pole mount"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Ruijie RG-AP680(CD) aliases and RG-AP680-IO specifications."
    products = PRODUCTS
    document_version = "Current official Ruijie product pages; accessed 2026-10-19"
    brand_name = "Ruijie"
