from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/85db7602afe445d4a475ec8483f714ad/M3T1A590N1245130106002341940/Huawei%20CloudEngine%20S6730-H-V2%20Series%2010GE%20Switches%20Datasheet.pdf"

PRODUCTS = {
    "S6730-H48X6C-V2": {
        "url": SOURCE_URL,
        "page": "Current model overview, service features, and hardware specifications",
        "title": "Huawei CloudEngine S6730-H-V2 Series 10GE Switches Datasheet",
        "values": {
            "switching_capacity_gbps": n(2160, "2.16 Tbps device switching capability; 2.4 Tbps system capability"),
            "packet_forwarding_rate_mpps": n(490),
            "packet_buffer_mb": n(18),
            "max_power_consumption_w": n(291, "100% throughput with fans at full speed"),
            "vlan_count": n(4094, "4K VLANs simultaneously"),
            "ip_interface_capacity": t("4K VLANIF interfaces simultaneously"),
            "routing_entry_capacity": t("Up to 256K IPv4 FIB entries and 80K IPv6 FIB entries"),
            "l2_features": t(
                "Access/trunk/hybrid VLAN ports; private VLAN; QinQ; VLAN stacking; LACP; "
                "M-LAG; Smart Link; LLDP; IGMP snooping; VXLAN and BGP EVPN"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; VBST; BPDU, root, and loop protection"),
            "stacking": t("Huawei iStack using service interfaces; up to 9 switches"),
            "stacking_units": n(9),
            "ospf_support": b(True, "OSPFv1/v2 and OSPFv3"),
            "rip_support": b(True, "RIPv1/v2 and RIPng"),
            "pbr_support": b(True),
            "multicast_routing": b(True, "IGMPv1/v2/v3; PIM-DM/PIM-SM/PIM-SSM"),
            "acl_security": t(
                "6.5K shared ingress/egress IPv4/IPv6 ACL hardware entries; NAC; port security; "
                "RADIUS/HWTACACS; DoS/flood defense; DAI; IP Source Guard"
            ),
            "management_methods": t(
                "CLI; console; Telnet; SSH; SNMPv1/v2c/v3; FTP/TFTP/SFTP; sFlow; "
                "OPS; streaming telemetry; cloud management; NETCONF/YANG"
            ),
            "secure_boot": b(True),
            "redundant_power": b(True, "Dual pluggable power modules with 1+1 redundancy"),
            "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
            "operating_temperature_c": t(
                "-5 to 45 °C at 0-1800 m; maximum temperature derates 1 °C per 220 m above 1800 m"
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and repair Huawei CloudEngine S6730-H48X6C-V2 specifications."
    products = PRODUCTS
    document_version = "Current official global datasheet; accessed 2026-10-20"
    brand_name = "Huawei"
