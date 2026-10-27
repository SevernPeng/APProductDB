from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/9568f7a74e9d44c19f2d70d08ba21fd3/M3T1A590N1246458575205826579/Huawei%20ekitEngine%20S310%20Series%20Switches%20Datasheet.pdf"

COMMON = {
    "management_methods": t(
        "Huawei eKit cloud management (NETCONF/YANG); Web system/HTTPS; CLI/Telnet; "
        "SSHv2; SNMPv1/v2/v3; RMON"
    ),
    "vlan_count": n(4094),
    "l2_features": t(
        "LACP; ERPS G.8032; Smart Link; MUX VLAN; VLAN stacking; IGMPv1/v2/v3 and MLD snooping"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU, root, and loop protection"
    ),
    "l3_features": t("IPv4/IPv6 static routing; PBR; OSPFv2/v3; VRRP; BFD"),
    "routing_entry_capacity": t("Up to 512 IPv4 FIB entries and 512 IPv6 FIB entries"),
    "stacking": t("Huawei iStack"),
    "operating_temperature_c": t("-5 to 50 °C (0-1800 m; derating above 1800 m)"),
}

PRODUCTS = {
    "S310-24ST4X": {
        "url": SOURCE_URL,
        "page": "Product specifications and service features tables",
        "title": "Huawei eKitEngine S310 Series Switches Datasheet",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(96),
            "max_power_consumption_w": n(41.7),
            "dimensions_mm": t("442 x 220 x 43.6 mm"),
        },
    },
    "S310-24T4X": {
        "url": SOURCE_URL,
        "page": "Service features and product specifications tables",
        "title": "Huawei eKitEngine S310 Series Switches Datasheet",
        "values": {
            "management_methods": COMMON["management_methods"],
            "vlan_count": COMMON["vlan_count"],
            "l2_features": COMMON["l2_features"],
            "stp_features": COMMON["stp_features"],
            "operating_temperature_c": COMMON["operating_temperature_c"],
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Huawei eKitEngine S310 residual switch specifications."
    products = PRODUCTS
    document_version = "Current official Huawei eKitEngine S310 series datasheet; accessed 2026-10-20"
    brand_name = "Huawei"
