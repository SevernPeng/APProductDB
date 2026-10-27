from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
    u,
)


MESH_GUIDE = "https://support.huawei.com/enterprise/zh/doc/EDOC1100457375/4366a8f"


PRODUCTS = {
    "AirEngine 5762-12": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/1d1ecaee0ed1493789c142f1220e9b2c/M3T1A590N1061724798907006996/%E5%8D%8E%E4%B8%BAAirEngine%205762-12%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf",
        "page": "Current official datasheet, pp. 5-11; Mesh support cross-checked in Huawei V200R024C10 configuration guide",
        "title": "Huawei AirEngine 5762-12 official product specifications",
        "values": {
            "max_clients": n(256),
            "max_ssids": n(16, "Per radio"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; DTLS"
            ),
        },
    },
    "AirEngine 5761-11": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/51d9432033204ad39eea5833f73b076f/M3T1A590N1247214429051473958/Huawei%20AirEngine%205761-11%20Access%20Point%20Datasheet.pdf",
        "page": "Current official datasheet, pp. 5-14; Mesh support cross-checked in Huawei V200R024C10 configuration guide",
        "title": "Huawei AirEngine 5761-11 official product specifications",
        "values": {
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5 dBi"),
            "mesh_support": b(True, "802.11ax Mesh on both service radios"),
            "fast_roaming": t("802.11k/v smart roaming; 802.11r fast roaming (≤50 ms)"),
            "wireless_security": t(
                "WEP; WPA2-PSK/802.1X; WPA3-SAE/802.1X; WPA-WPA2 and WPA2-WPA3 mixed modes; "
                "WPA2-PPSK; WAPI; PMF; WIDS/WIPS; IPsec/DTLS"
            ),
            "wireless_range": u("Removed malformed scraped fragment; official datasheet does not publish a range figure"),
        },
    },
    "AirEngine 5760-51": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AP radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(True, "802.11ax Mesh on all three radios")},
    },
    "AirEngine 5761R-11": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AP radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(True, "802.11ax Mesh on both service radios")},
    },
    "AirEngine 5761R-11E": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AP radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(True, "802.11ax Mesh on both service radios")},
    },
    "AirEngine 5762C-10": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AirEngine 5762C-10-V2 radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(False, "AirEngine 5762C-10-V2 does not support Mesh")},
    },
    "AirEngine 6760R-51": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AP radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(True, "802.11ax Mesh on both service radios")},
    },
    "AirEngine 6760R-51E": {
        "url": MESH_GUIDE,
        "page": "Table 15-2, AP radio protocol types used for Mesh links",
        "title": "Huawei WLAN V200R024C10 Mesh compatibility documentation",
        "values": {"mesh_support": b(True, "802.11ax Mesh on both service radios")},
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei AP specifications and Mesh support records."
    products = PRODUCTS
    document_version = "Current official Huawei datasheets and V200R024C10 configuration guide; accessed 2026-10-19"
    brand_name = "Huawei"
