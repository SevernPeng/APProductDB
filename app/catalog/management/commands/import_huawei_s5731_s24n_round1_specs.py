from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/ff1febef8ee34c8aabbbaca7c8ae4cc1/M2T1A590N1002264988344000526/%E5%8D%8E%E4%B8%BA%20CloudEngine%20S5731-S%E7%B3%BB%E5%88%97%E5%A4%9A%E9%80%9F%E7%8E%87%E4%BA%A4%E6%8D%A2%E6%9C%BA%E5%BD%A9%E9%A1%B5.pdf"

PRODUCTS = {
    # The database's suffix-less record corresponds to Huawei's current
    # S5731-S24N4X2Q-A (built-in AC power) model.
    "S5731-S24N4X2Q": {
        "url": SOURCE_URL,
        "page": "Current S5731-S24N4X2Q-A hardware and service-feature tables",
        "title": "Huawei CloudEngine S5731-S Series Multi-GE Switches Brochure",
        "values": {
            "max_power_consumption_w": n(134),
            "vlan_count": n(4094, "4K VLANs"),
            "l2_features": t(
                "Guest/voice/MUX VLAN; GVRP; MAC/protocol/IP-subnet/policy/port VLAN assignment; "
                "VLAN mapping; LACP; Smart Link; SEP; ERPS; IGMP snooping; VXLAN and BGP EVPN"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU, root, and loop protection; VBST"),
            "stacking": t("Huawei intelligent iStack; up to 9 switches"),
            "ospf_support": b(True, "OSPF and OSPFv3"),
            "rip_support": b(True, "RIPv1/v2 and RIPng"),
            "acl_security": t(
                "Layer 2-4 ACL filtering; 802.1X; AAA/RADIUS/HWTACACS; NAC; IP/MAC/port/VLAN binding; "
                "port isolation/security; DoS/ARP/ICMP defense; SSHv2; HTTPS; secure boot"
            ),
            "management_methods": t(
                "SNMPv1/v2c/v3; RMON; web NMS; system logs and alarms; NetStream; telemetry; "
                "cloud management; OPS; NETCONF"
            ),
            "dimensions_mm": t("442 x 220 x 43.6 mm (W x D x H)"),
            "operating_temperature_c": t("-5 to 45 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import Huawei S5731-S24N4X2Q specs from the current -A model brochure."
    products = PRODUCTS
    document_version = "Official 2024 Chinese brochure for current S5731-S24N4X2Q-A; accessed 2026-10-20"
    brand_name = "Huawei"
