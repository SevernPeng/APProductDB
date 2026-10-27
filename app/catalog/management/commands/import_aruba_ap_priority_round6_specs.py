from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaApImportCommand,
    n,
    t,
)


URL_740 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20740%20Series%20Campus%20Access%20Points%20QuickSpecs-a50009243enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a50009243enw.pdf&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=2"
URL_760 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20760%20Series%20Hardened%20Access%20Points%20QuickSpecs-a50009245enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a50009245enw.pdf&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=2"


PRODUCTS = {
    "AP-745": {
        "url": URL_740,
        "page": "2-8, 12-15",
        "title": "HPE Aruba Networking 740 Series Campus Access Points QuickSpecs, version 2",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(344, "2.4 GHz: up to 344 Mbps with 2SS EHT20"),
            "rate_5g_mbps": n(2880, "5 GHz: up to 2.88 Gbps with 4SS EHT80"),
            "rate_6g_mbps": n(5760, "6 GHz: up to 5.76 Gbps with 4SS EHT160"),
            "total_spatial_streams": n(10, "2x2 on 2.4 GHz plus 4x4 on 5 GHz and 6 GHz"),
            "mimo_2g": t("2x2 SU-MIMO and UL/DL MU-MIMO"),
            "mimo_5g": t("4x4 SU-MIMO and UL/DL MU-MIMO"),
            "mimo_6g": t("4x4 SU-MIMO and UL/DL MU-MIMO"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(512, "Up to 512 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 100/1000/2500/5000BASE-T RJ45; USB 2.0 host; micro-B USB serial console"),
            "power_method": t("IEEE 802.3at/bt PoE; 802.3af supported for staging only"),
            "max_power_consumption_w": n(26, "Maximum worst-case without USB load: 26 W; 36 W with USB load"),
            "dimensions_mm": t("240 x 240 x 57 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Integrated downtilt omnidirectional antennas for 4x4 MIMO; 2x2 on 2.4 GHz"),
            "antenna_gain_dbi": t("2.4 GHz: 5.9 dBi; 5 GHz: 5.9 dBi; 6 GHz: 5.4 dBi"),
            "centralized_management": t("HPE Aruba Networking Central with AOS-10"),
            "fast_roaming": t("AI-powered Central ClientMatch steering and AirMatch enhanced roaming"),
        },
    },
    "AP-765": {
        "url": URL_760,
        "page": "3-7, 16-21",
        "title": "HPE Aruba Networking 760 Series Hardened Access Points QuickSpecs, version 2",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz (two concurrent flexible radios)"),
            "rate_2g_mbps": n(688, "2.4 GHz: up to 688 Mbps with 2SS EHT40"),
            "rate_5g_mbps": n(2880, "5 GHz: up to 2.88 Gbps in optional 4x4 EHT80 mode"),
            "rate_6g_mbps": n(5760, "6 GHz: up to 5.76 Gbps in optional 4x4 EHT160 mode"),
            "total_spatial_streams": n(4, "Two concurrent 2x2 flexible radios; optional single-radio 4x4 mode"),
            "mimo_2g": t("2x2 MIMO with UL/DL MU-MIMO"),
            "mimo_5g": t("2x2 MIMO dual-radio mode or 4x4 MIMO single-radio mode; UL/DL MU-MIMO"),
            "mimo_6g": t("2x2 MIMO dual-radio mode or 4x4 MIMO single-radio mode; UL/DL MU-MIMO"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(400, "Up to 400 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 100/1000/2500/5000BASE-T RJ45 with MACsec; USB 2.0 Type-C host; micro-B USB console"),
            "power_method": t("IEEE 802.3at/bt PoE; unrestricted with 802.3bt class 5; 802.3af staging only"),
            "max_power_consumption_w": n(25.5, "Maximum worst-case without USB load: 25.5 W; up to 34.5 W with 802.3bt class 5 and USB load"),
            "dimensions_mm": t("266.4 x 174 x 100 mm without mount bracket"),
            "operating_temperature_c": t("-40 to 65 °C with solar cover; -40 to 55 °C without solar cover"),
            "ip_rating": t("IP66/IP67"),
            "antenna_type": t("Integrated dynamic omnidirectional or 90° x 90° directional antennas; 2x2/4x4 modes"),
            "antenna_gain_dbi": t("Omni: 2.8 dBi (2.4 GHz), 3.9/3.0 dBi (5 GHz 2x2/4x4), 3.3/3.2 dBi (6 GHz 2x2/4x4); directional: 6.1, 6.0/6.1, 7.4/7.2 dBi"),
            "centralized_management": t("HPE Aruba Networking Central with AOS-10"),
            "fast_roaming": t("AI-powered ClientMatch steering and AirMatch enhanced roaming"),
        },
    },
}


class Command(ArubaApImportCommand):
    help = "Import manually verified Aruba AP-745 and AP-765 specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking QuickSpecs; accessed 2026-10-16"
