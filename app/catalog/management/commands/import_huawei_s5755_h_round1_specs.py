from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/0d3b90a9b98d4062a4abde8bfbf30498/M3T1A590N1245325043171459291/%E5%8D%8E%E4%B8%BA%20CloudEngine%20S5755-H%E7%B3%BB%E5%88%97%E9%AB%98%E5%93%81%E8%B4%A82_5GE%E4%BA%A4%E6%8D%A2%E6%9C%BA%E5%BD%A9%E9%A1%B5.pdf"

COMMON = {
    "vlan_count": n(4094, "4K VLANs"),
    "jumbo_frame_bytes": n(9216, "Jumbo Frames: 9216 Bytes"),
    "l2_features": t(
        "Voice/MUX/super/sub VLAN; VLAN stacking and mapping; GVRP; QinQ; SmartLink; SEP; "
        "ERPS G.8032; IGMPv1/v2/v3 and MLD snooping"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; VBST; BPDU, root, and loop protection"
    ),
    "routing_entry_capacity": t("Up to 192K IPv4 FIB entries and 96K IPv6 FIB entries"),
    "ospf_support": b(True),
    "rip_support": b(True),
    "pbr_support": b(True),
    "multicast_routing": b(True, "PIM-DM/PIM-SM/PIM-SSM; IPv4 and IPv6 multicast routing"),
    "acl_security": t(
        "Layer 2-4 ACL filtering; 802.1X/MAC/Portal authentication; ARP/ND snooping and DAI; "
        "IPSG; port isolation/security; DoS/ARP/ICMP and CPU protection; SSHv2; HTTPS; MACsec"
    ),
    "management_methods": t(
        "Huawei iStack; SNMPv1/v2c/v3; NETCONF/YANG cloud management; eSight; Web NMS; "
        "RMON; telemetry; RESTCONF; gRPC; Telnet/SSH; SFTP/TFTP"
    ),
    "stacking": t("Huawei iStack; two or more switches can operate as one logical switch"),
    "power_supply": t("Built-in AC power supply, front-access design"),
    "dimensions_mm": t("442 x 220 x 43.6 mm (W x D x H)"),
    "operating_temperature_c": t("-5 to 45 °C"),
}

PRODUCTS = {
    "S5755-H24N4Y-A": {
        "url": SOURCE_URL,
        "page": "2026 model, hardware, and service-feature tables",
        "title": "Huawei CloudEngine S5755-H Series High-Quality 2.5GE Switches Datasheet",
        "values": {
            **COMMON,
            "max_power_consumption_w": n(69, "ATIS 100% traffic load"),
        },
    },
    "S5755-H48N4Y-A": {
        "url": SOURCE_URL,
        "page": "2026 model, hardware, and service-feature tables",
        "title": "Huawei CloudEngine S5755-H Series High-Quality 2.5GE Switches Datasheet",
        "values": {
            **COMMON,
            "max_power_consumption_w": n(105, "ATIS 100% traffic load"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current Huawei CloudEngine S5755-H N4Y-A specifications."
    products = PRODUCTS
    document_version = "Official 2026 Chinese datasheet; accessed 2026-10-20"
    brand_name = "Huawei"
