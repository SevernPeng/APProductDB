from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


PRODUCTS = {
    "AirEngine 5762-10": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/7ffbc6ef5aff483c8648d38fa1de306c/M3T1A590N1062665325714358468/Huawei%20AirEngine%205762-10%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet; Mesh support cross-checked in Huawei WLAN configuration guide",
        "title": "Huawei AirEngine 5762-10 official product specifications",
        "values": {
            "max_clients": n(256),
            "max_ssids": n(16, "Per radio"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; DTLS"
            ),
        },
    },
    "AirEngine 5761-21": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/8cdbfaed42fb40f6a3887875d353f1da/M3T1A590N1142844091807498326/Huawei%20AirEngine%205761-21%20Access%20Point%20Datasheet.pdf",
        "page": "Current official product datasheet; Mesh support cross-checked in Huawei WLAN configuration guide",
        "title": "Huawei AirEngine 5761-21 official product specifications",
        "values": {
            "max_ssids": n(16, "Per radio"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; IPsec/DTLS"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AirEngine 5762-10 and 5761-21 specifications."
    products = PRODUCTS
    document_version = "Current official Huawei datasheets and V200R024C10 configuration guide; accessed 2026-10-19"
    brand_name = "Huawei"
