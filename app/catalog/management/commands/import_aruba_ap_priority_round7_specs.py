from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaApImportCommand,
    n,
    t,
)


URL_720H = "https://www.hpe.com/psnow/downloadDoc/HPE%20Networking%20720H%20Series%20Hospitality%20Access%20Points%20QuickSpecs-a50009259enw.pdf?deepLink=&form=false&hf=regular&id=a50009259enw.pdf&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=1"


COMMON = {
    "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
    "max_clients": n(400, "Up to 400 associated client devices per radio"),
    "max_ssids": n(16, "Up to 16 BSSIDs per radio"),
    "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
    "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
    "mimo_6g": t("2x2 SU-MIMO and MU-MIMO"),
    "operating_temperature_c": t("0 to 40 °C"),
    "fast_roaming": t("AI-powered ClientMatch steering and AirMatch radio optimization"),
    "wireless_security": t("WPA2/WPA3 Enterprise and Personal; Enhanced Open (OWE); WPA2-MPSK"),
}


PRODUCTS = {
    "AP-721H": {
        "url": URL_720H,
        "page": "1-7, 12-18, 28-29",
        "title": "HPE Networking 720H Series Hospitality Access Points QuickSpecs, version 1",
        "values": {
            **COMMON,
            "rate_2g_mbps": n(344, "2.4 GHz: up to 344 Mbps with 2SS EHT20"),
            "rate_5g_mbps": n(1400, "5 GHz: up to 1.4 Gbps with 2SS EHT80"),
            "rate_6g_mbps": n(2800, "6 GHz: up to 2.8 Gbps with 2SS EHT160"),
            "total_spatial_streams": n(4, "Two concurrent 2x2 radios across three supported bands"),
            "max_channel_width_mhz": n(160),
            "ethernet_interfaces": t("1 x 100/1000BASE-T uplink; 1 x 10/100/1000BASE-T downlink; micro-B USB serial console"),
            "poe_output": t("No PoE output / PSE", "AP-721H is PoE-PD class 3 only; the peak-power table lists PSE as N/A"),
            "power_method": t("IEEE 802.3af PoE class 3"),
            "max_power_consumption_w": n(5.64, "Peak active power draw: 5.64 W"),
            "dimensions_mm": t("90 x 32 x 170 mm"),
            "centralized_management": t("HPE Aruba Networking Central with AOS 10.8.1.0; standalone or gateway operation"),
        },
    },
    "AP-723H": {
        "url": URL_720H,
        "page": "1-7, 12-18, 28-29",
        "title": "HPE Networking 720H Series Hospitality Access Points QuickSpecs, version 1",
        "values": {
            **COMMON,
            "rate_2g_mbps": n(344, "2.4 GHz: up to 344 Mbps with 2SS EHT20"),
            "rate_5g_mbps": n(1400, "5 GHz: up to 1.4 Gbps with 2SS EHT80"),
            "rate_6g_mbps": n(2800, "6 GHz: up to 2.8 Gbps with 2SS EHT160"),
            "total_spatial_streams": n(6, "Three concurrent 2x2 radios"),
            "max_channel_width_mhz": n(160),
            "ethernet_interfaces": t("1 x 100/1000/2500BASE-T uplink; 2 x 10/100/1000BASE-T downlink; USB 2.0 host; micro-B USB serial console"),
            "poe_output": t("No PoE output / PSE", "AP-723H is PoE-PD class 4 only; the peak-power table lists PSE as N/A"),
            "power_method": t("48 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(9.78, "Peak active power draw: 9.78 W; 15.40 W with USB load"),
            "dimensions_mm": t("130 x 32 x 180 mm"),
            "centralized_management": t("Dual-platform: HPE Aruba Networking Central (AOS 10.8.1.0) or HPE Mist 16.x"),
        },
    },
    "AP-725H": {
        "url": URL_720H,
        "page": "1-7, 12-18, 28-29",
        "title": "HPE Networking 720H Series Hospitality Access Points QuickSpecs, version 1",
        "values": {
            **COMMON,
            "rate_2g_mbps": n(688, "2.4 GHz: up to 688 Mbps with 2SS EHT40"),
            "rate_5g_mbps": n(2800, "5 GHz: up to 2.8 Gbps with 2SS EHT160"),
            "rate_6g_mbps": n(5800, "6 GHz: up to 5.8 Gbps with 2SS EHT320"),
            "total_spatial_streams": n(6, "Three concurrent 2x2 radios"),
            "max_channel_width_mhz": n(320),
            "ethernet_interfaces": t("1 x 100/1000/2500/5000BASE-T uplink; 4 x 10/100/1000BASE-T downlink; USB 2.0 host; micro-B USB serial console"),
            "poe_output": t("E1/E2 support dual IEEE 802.3af output or single IEEE 802.3at output on E1; 30 W maximum"),
            "power_method": t("48 V DC or IEEE 802.3af/at/bt PoE; unrestricted with DC or 802.3bt class 6"),
            "max_power_consumption_w": n(10.76, "Peak active AP draw: 10.76 W; up to 46.88 W with USB and class 4 PSE loads"),
            "dimensions_mm": t("130 x 32 x 180 mm"),
            "centralized_management": t("HPE Aruba Networking Central with AOS 10.8.1.0; standalone or gateway operation"),
        },
    },
}


class Command(ArubaApImportCommand):
    help = "Import manually verified Aruba AP-721H, AP-723H, and AP-725H specifications."
    products = PRODUCTS
    document_version = "Official HPE Networking QuickSpecs version 1 (2026-05-04); accessed 2026-10-16"
