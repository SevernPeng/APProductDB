from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaApImportCommand,
    n,
    t,
)


URL_600H = "https://www.hpe.com/us/en/collaterals/collateral.a50007032enw.html"
URL_730 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20730%20Series%20Campus%20Access%20Points%20QuickSpecs-a50009206enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a50009206enw.pdf&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=8"
URL_750 = "https://www.hpe.com/asia_pac/en/collaterals/collateral.a50009211enw.html"


PRODUCTS = {
    "AP-605H": {
        "url": URL_600H,
        "page": "Specifications; current HTML revision",
        "title": "HPE Aruba Networking 600H Series Hospitality Access Points QuickSpecs",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz (two concurrent radios)"),
            "rate_2g_mbps": n(574, "2.4 GHz: up to 574 Mbps with 2SS HE40; 287 Mbps with HE20"),
            "rate_5g_mbps": n(1200, "5 GHz: up to 1.2 Gbps with 2SS HE80"),
            "rate_6g_mbps": n(2400, "6 GHz: up to 2.4 Gbps with 2SS HE160"),
            "total_spatial_streams": n(4, "Two concurrent 2x2 radios; tri-band capable"),
            "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_6g": t("2x2 SU-MIMO and MU-MIMO"),
            "max_channel_width_mhz": n(160, "HE160 on 6 GHz"),
            "max_clients": n(512, "Up to 512 associated client devices per radio"),
            "max_ssids": n(16, "Up to 16 BSSIDs per radio; limited to 8 on 6 GHz"),
            "ethernet_interfaces": t("1 x 100/1000/2500BASE-T uplink; 4 x 10/100/1000BASE-T downlink; USB 2.0; micro-B USB console"),
            "poe_output": t("PoE-PSE on E1/E2; with 802.3at input, 802.3af output is available on E1 only"),
            "power_method": t("48 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(14.9, "AP-only maximum: 14.9 W DC or 13.9 W PoE; USB and PoE-PSE loads excluded"),
            "dimensions_mm": t("105 x 40 x 153 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "centralized_management": t("HPE Aruba Networking Central cloud/on-premises with AOS-10"),
            "fast_roaming": t("AI-powered ClientMatch client steering and load balancing"),
            "wireless_security": t("WPA3 and Enhanced Open; WPA2-MPSK"),
        },
    },
    "AP-735": {
        "url": URL_730,
        "page": "4-6, 13-16",
        "title": "HPE Aruba Networking 730 Series Campus Access Points QuickSpecs, version 8",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(688, "2.4 GHz: up to 688 Mbps with 2SS EHT40"),
            "rate_5g_mbps": n(2900, "5 GHz: up to 2.9 Gbps with 2SS EHT160"),
            "rate_6g_mbps": n(5800, "6 GHz: up to 5.8 Gbps with 2SS EHT320"),
            "total_spatial_streams": n(6, "Three concurrent 2x2 radios"),
            "mimo_2g": t("2x2 MIMO with UL/DL MU-MIMO"),
            "mimo_5g": t("2x2 MIMO with UL/DL MU-MIMO"),
            "mimo_6g": t("2x2 MIMO with UL/DL MU-MIMO"),
            "max_channel_width_mhz": n(320, "EHT320 on 6 GHz"),
            "max_clients": n(512, "Up to 512 associated client devices per radio, current version 8"),
            "ethernet_interfaces": t("2 x 100/1000/2500/5000BASE-T Smart Rate RJ45 with LACP; 2 x USB 2.0; micro-B USB console"),
            "power_method": t("12 V DC or dual IEEE 802.3at/bt PoE; unrestricted with 802.3bt class 5"),
            "max_power_consumption_w": n(24, "AP-only worst-case PoE consumption: 24 W; 36 W with USB loads"),
            "dimensions_mm": t("240 x 240 x 56 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Integrated downtilt omnidirectional antennas for 2x2 MIMO"),
            "antenna_gain_dbi": t("2.4 GHz: 5.1 dBi; 5 GHz: 5.5 dBi; 6 GHz: 5.3 dBi"),
            "centralized_management": t("HPE Aruba Networking Central with cloud-native AOS-10"),
            "fast_roaming": t("AI-powered ClientMatch steering and AirMatch radio optimization"),
        },
    },
    "AP-755": {
        "url": URL_750,
        "page": "Specifications; HTML version 11, 17-Aug-2026",
        "title": "HPE Aruba Networking 750 Series Campus Access Points QuickSpecs, version 11",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(1400, "2.4 GHz: up to 1.4 Gbps with 4SS EHT40"),
            "rate_5g_mbps": n(5800, "5 GHz: up to 5.8 Gbps with 4SS EHT160"),
            "rate_6g_mbps": n(11500, "6 GHz: up to 11.5 Gbps with 4SS EHT320"),
            "total_spatial_streams": n(12, "Three concurrent 4x4 radios"),
            "mimo_2g": t("4x4 MIMO with UL/DL MU-MIMO"),
            "mimo_5g": t("4x4 MIMO with UL/DL MU-MIMO"),
            "mimo_6g": t("4x4 MIMO with UL/DL MU-MIMO"),
            "max_channel_width_mhz": n(320, "EHT320 on 6 GHz"),
            "max_clients": n(512, "Up to 512 associated client devices per radio, current version 11"),
            "ethernet_interfaces": t("2 x 100/1000/2500/5000/10000BASE-T Smart Rate RJ45 with LACP; 2 x USB 2.0; micro-B USB console"),
            "power_method": t("12 V DC or dual IEEE 802.3af/at/bt PoE; unrestricted with 802.3bt class 6"),
            "max_power_consumption_w": n(40, "AP-only worst-case PoE consumption: 40 W; 51 W with USB loads"),
            "dimensions_mm": t("260 x 260 x 57 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Integrated downtilt omnidirectional antennas for 4x4 MIMO"),
            "antenna_gain_dbi": t("2.4 GHz: 5.3 dBi; 5 GHz: 6.0 dBi; 6 GHz: 6.0 dBi"),
            "centralized_management": t("HPE Aruba Networking Central with AOS-10"),
            "fast_roaming": t("AI-powered ClientMatch steering and AirMatch radio optimization"),
        },
    },
}


class Command(ArubaApImportCommand):
    help = "Import manually verified Aruba AP-605H, AP-735, and AP-755 specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking QuickSpecs; accessed 2026-10-16"
