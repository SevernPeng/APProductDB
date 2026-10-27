from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/74dd87cc705d4866ad87512921e9d929/M3T1A590N1159881877131128966/Huawei%20CloudEngine%20S6730-H%20Series%2025GE%20Switches%20Datasheet.pdf"

PRODUCTS = {
    "S6730-H28Y4C": {
        "url": SOURCE_URL,
        "page": "Model overview, function/feature matrix, and hardware specifications",
        "title": "Huawei CloudEngine S6730-H Series 25GE Switches Datasheet",
        "values": {
            "switching_capacity_gbps": n(2200, "2.2 Tbps device switching capability; 2.4 Tbps system capability"),
            "packet_forwarding_rate_mpps": n(490),
            "max_power_consumption_w": n(253, "100% throughput with fans at full speed"),
            "vlan_count": n(4094),
            "ip_interface_capacity": t("4094 VLANIF interfaces"),
            "routing_entry_capacity": t("Up to 256K IPv4 routes and 80K IPv6 routes (shared resources)"),
            "l2_features": t(
                "Access/trunk/hybrid and QinQ VLAN ports; link aggregation; LLDP; Smart Link; "
                "SEP; ERPS; IGMP/MLD snooping; VXLAN and BGP EVPN"
            ),
            "stp_features": t("STP; RSTP; MSTP; VBST; BPDU, root, loop, and TC-BPDU attack protection"),
            "stacking": t("Huawei iStack using service interfaces; up to 9 switches"),
            "stacking_bandwidth_gbps": n(1200, "Up to 1.2 Tbit/s bidirectional"),
            "stacking_units": n(9),
            "ospf_support": b(True),
            "rip_support": b(True, "RIPv1, RIPv2, and RIPng"),
            "pbr_support": b(True),
            "multicast_routing": b(True, "IGMPv1/v2/v3; PIM-DM/PIM-SM; MSDP; IPv4 and IPv6 multicast routing"),
            "acl_security": t(
                "Up to 6K shared IPv4/IPv6 ACL rules; Layer 2-4 and user-defined ACLs; "
                "802.1X/MAC/Portal authentication; ARP and DHCP snooping defenses; MACsec"
            ),
            "management_methods": t(
                "CLI; console; Telnet; SSH; SNMP; web management; EasyDeploy; SVF; "
                "cloud management; OPS; NETCONF/YANG"
            ),
            "secure_boot": b(True),
            "redundant_power": b(True, "Dual pluggable power modules with 1+1 redundancy"),
            "dimensions_mm": t("442 x 220 x 43.6 mm (W x D x H)"),
            "operating_temperature_c": t(
                "-5 to 45 °C at 0-1800 m; maximum temperature derates 1 °C per 220 m above 1800 m"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and repair Huawei CloudEngine S6730-H28Y4C specifications."
    products = PRODUCTS
    document_version = "Official global detailed datasheet; accessed 2026-10-20"
    brand_name = "Huawei"
