from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


MESH_GUIDE = "https://support.huawei.com/enterprise/zh/doc/EDOC1100457375/4366a8f"


PRODUCTS = {
    "AirEngine 5762-13W": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/3f1965434c7c4c1fb2a857c5721af86a/M3T1A590N1061725108952784993/%E5%8D%8E%E4%B8%BAAirEngine%205762-13W%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf",
        "page": "Current official datasheet, pp. 5-11; Mesh support cross-checked in Huawei V200R024C10 configuration guide",
        "title": "Huawei AirEngine 5762-13W official product specifications",
        "values": {
            "max_ssids": n(16, "Per radio"),
            "antenna_gain_dbi": t("2.4 GHz: 2 dBi; 5 GHz: 3 dBi"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; DTLS; TPM"
            ),
        },
    },
    "AirEngine 5762-12SW": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/2a252cec705b44d5bb45e9876bf88b7e/M3T1A590N1062665920415138003/Huawei%20AirEngine%205762-12SW%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, pp. 2-10; Mesh support cross-checked in Huawei V200R024C10 configuration guide",
        "title": "Huawei AirEngine 5762-12SW official product specifications",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 2 dBi; 5 GHz: 3 dBi"),
            "centralized_management": t("Huawei WLAN AC in Fit mode; Fat mode; Huawei cloud management platform"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; DTLS"
            ),
        },
    },
    "AirEngine 5761R-11": {
        "url": "https://e-file.huawei.com/en/material/MaterialDownload?id=dc42446652d94f859af65e6c7cc09fd7&language=en&type=material",
        "page": "Current official combined datasheet, pp. 4-7",
        "title": "Huawei AirEngine 5761R-11 and 5761R-11E official product specifications",
        "values": {
            "centralized_management": t("Huawei WLAN AC in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
        },
    },
    "AirEngine 5761R-11E": {
        "url": "https://e-file.huawei.com/en/material/MaterialDownload?id=dc42446652d94f859af65e6c7cc09fd7&language=en&type=material",
        "page": "Current official combined datasheet, pp. 4-10",
        "title": "Huawei AirEngine 5761R-11 and 5761R-11E official product specifications",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 11 dBi", "With the ANTDG0407A1NS external antenna specified in the datasheet"),
            "centralized_management": t("Huawei WLAN AC in Fit mode; Fat mode; Huawei cloud management platform"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei wall-plate and outdoor AP specifications."
    products = PRODUCTS
    document_version = "Current official Huawei datasheets and V200R024C10 configuration guide; accessed 2026-10-19"
    brand_name = "Huawei"
