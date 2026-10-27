from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaApImportCommand,
    na,
    n,
    t,
)


URL_503 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20503%20Series%20Campus%20Access%20Points%20QuickSpecs-a50006989enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a50006989enw.pdf&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=9"
URL_580 = "https://www.hpe.com/tw/en/collaterals/collateral.a50004278enw.html"


OUTDOOR_580_COMMON = {
    "supported_bands": t("2.4 GHz / 5 GHz"),
    "rate_2g_mbps": n(1150, "2.4 GHz: up to 1,150 Mbps with 4SS HE40"),
    "rate_5g_mbps": n(2400, "5 GHz: up to 2.4 Gbps with 4SS HE80 or 2SS HE160"),
    "total_spatial_streams": n(8, "Four spatial streams on each service radio"),
    "mimo_2g": t("4x4 SU-MIMO and MU-MIMO"),
    "mimo_5g": t("4x4 SU-MIMO and MU-MIMO"),
    "max_channel_width_mhz": n(160, "HE160 supported on 5 GHz"),
    "max_clients": n(1024, "Up to 1,024 associated client devices per radio"),
    "ethernet_interfaces": t("1 x 100/1000/2500/5000BASE-T Smart Rate; 1 x 10GBASE-R SFP+; 1 x 10/100/1000BASE-T with PoE output; USB-C console"),
    "power_method": t("110-240 V AC or IEEE 802.3af/at/bt PoE; unrestricted with AC or 802.3bt class 6"),
    "max_power_consumption_w": n(71, "Maximum worst-case: 71 W AC; 49.5 W with 802.3bt class 6 PoE"),
    "operating_temperature_c": t("-40 to 65 °C with full solar loading"),
    "ip_rating": t("IP66/IP67"),
    "centralized_management": t("HPE Aruba Networking Central cloud/on-premises, standalone, or gateway operation; AOS 8/10"),
    "fast_roaming": t("AI-powered ClientMatch steering and AirMatch enhanced roaming"),
}


PRODUCTS = {
    "AP-503": {
        "url": URL_503,
        "page": "1-4, 9-12",
        "title": "HPE Aruba Networking 503 Series Campus Access Points QuickSpecs, version 9",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "2.4 GHz: up to 574 Mbps with 2SS HE40; 287 Mbps with HE20"),
            "rate_5g_mbps": n(1200, "5 GHz: up to 1.2 Gbps with 2SS HE80"),
            "total_spatial_streams": n(4, "Two spatial streams on each service radio"),
            "mimo_2g": t("2x2 SU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO"),
            "max_channel_width_mhz": n(80, "HE80 maximum"),
            "max_clients": n(256, "Up to 256 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; USB 2.0 host; micro-B USB serial console"),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(10.9, "Maximum worst-case excluding USB load: 10.9 W"),
            "dimensions_mm": t("145 x 145 x 35 mm without mount bracket"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Integrated downtilt omnidirectional antennas for 2x2 MIMO"),
            "antenna_gain_dbi": t("2.4 GHz: 1.7 dBi; 5 GHz: 4.8 dBi"),
            "centralized_management": t("HPE Aruba Networking Central cloud/on-premises; AOS/InstantOS 8.11.1.0 or AOS 10.5.0.0"),
            "fast_roaming": t("AI-powered ClientMatch steering and AirMatch radio optimization"),
        },
    },
    "AP-584": {
        "url": URL_580,
        "page": "Technical Specifications; HTML version 13, 17-Aug-2026",
        "title": "HPE Aruba Networking 580 Series Outdoor Access Points QuickSpecs, version 13",
        "values": {
            **OUTDOOR_580_COMMON,
            "dimensions_mm": t("324 x 312 x 244 mm"),
            "antenna_type": t("Four N-female connectors for external dual-band Wi-Fi antennas; one N-female connector for BLE/Zigbee antenna"),
            "antenna_gain_dbi": na("External-antenna model; Wi-Fi antenna gain depends on the selected external antennas. The included BLE/Zigbee antenna is rated at 5 dBi."),
        },
    },
    "Ap-587": {
        "url": URL_580,
        "page": "Technical Specifications; HTML version 13, 17-Aug-2026",
        "title": "HPE Aruba Networking 580 Series Outdoor Access Points QuickSpecs, version 13",
        "values": {
            **OUTDOOR_580_COMMON,
            "dimensions_mm": t("302 x 300 x 174 mm"),
            "antenna_type": t("Four integrated 90° H x 90° V dual-band directional antennas for 4x4 MIMO"),
            "antenna_gain_dbi": t("2.4 GHz: 5.8 dBi; 5 GHz: 6.6 dBi"),
        },
    },
}


class Command(ArubaApImportCommand):
    help = "Import manually verified Aruba AP-503, AP-584, and AP-587 specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking QuickSpecs; accessed 2026-10-16"
