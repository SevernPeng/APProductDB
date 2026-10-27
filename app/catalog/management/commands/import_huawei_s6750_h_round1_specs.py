from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/mx/documents/products/enterprise-network/1b3e12e7dd55479aa64f2f5a4163e773"
CURRENT_DATASHEET_URL = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "9d6f594a0e254c26a020e2fc107adb4f/M3T1A590N1200751274737987732/"
    "Huawei%20CloudEngine%20S6750-H%20Series%2025GE%20Switches%20Datasheet_25H2.pdf"
)

PRODUCTS = {
    "S6750-H36C": {
        "url": CURRENT_DATASHEET_URL,
        "page": "Model overview, hardware specifications, and functions/features table",
        "title": "Huawei CloudEngine S6750-H Series 100GE Switches Brochure",
        "values": {
            "switching_capacity_gbps": n(7200, "7.2 Tbps device switching capability; 8 Tbps system capability"),
            "packet_forwarding_rate_mpps": n(1200),
            "max_power_consumption_w": n(
                679,
                "Worst case at 45 °C, 100% traffic, long-distance optical modules, and dual power modules; 558 W at standard 100% traffic",
            ),
            "vlan_count": n(4094, "4K VLANs"),
            "jumbo_frame_bytes": n(9500, "Jumbo frames: 9500 bytes"),
            "ip_interface_capacity": t(
                "4K VLANIF interfaces simultaneously",
                "Official feature table: 4K VLANif interface simultaneously",
            ),
            "l2_features": t(
                "Access/trunk/hybrid VLAN ports; QinQ and selective QinQ; VLAN stacking and mapping; "
                "MAC learning; M-LAG; Smart Link; LLDP; IGMP snooping; VXLAN and BGP EVPN"
            ),
            "stp_features": t("STP; RSTP; MSTP; VBST; BPDU, root, and loop protection; G.8032 ERPS"),
            "stacking": t("Huawei iStack using service ports; up to 9 switches"),
            "ospf_support": b(True, "OSPF and OSPFv3"),
            "rip_support": b(True, "RIP and RIPng"),
            "pbr_support": b(True),
            "acl_security": t(
                "ACL/CAR; NAC; 802.1X and MAC authentication; RADIUS/HWTACACS; MACsec; "
                "DoS/flood defense; IPv6 RA Guard; secure boot"
            ),
            "management_methods": t(
                "CLI; console; Telnet; SSH; SNMPv1/v2c/v3; FTP/TFTP/SFTP; RMON; "
                "OPS; streaming telemetry; cloud management; NETCONF"
            ),
            "fanless": b(False, "Five pluggable fan modules with fan redundancy"),
            "redundant_power": b(True, "Dual pluggable AC or DC power modules with 1+1 redundancy"),
            "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
            "operating_temperature_c": t("-5 to 45 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and repair Huawei CloudEngine S6750-H36C specifications."
    products = PRODUCTS
    document_version = "Official S6750-H 25GE datasheet (25H2, published 2025); accessed 2026-10-23"
    brand_name = "Huawei"
