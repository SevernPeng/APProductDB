from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/fd4050fcc5654b46ba93017bf8e5d3fd/M3T1A590N1164618303599407310/Huawei%20CloudEngine%206863H-48S6CQ%20Switch%20Datasheet.pdf"

PRODUCTS = {
    "CE6863H-48S6CQ": {
        "url": SOURCE_URL,
        "page": "Product, hardware, and performance/scalability specifications",
        "title": "Huawei CloudEngine 6863H Switch Datasheet",
        "values": {
            "switching_capacity_gbps": n(3600),
            "packet_forwarding_rate_mpps": n(954),
            "packet_buffer_mb": n(42),
            "max_power_consumption_w": n(384),
            "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
            "operating_temperature_c": t(
                "0 to 40 °C at 0-1800 m; maximum temperature derates 1 °C per 220 m above 1800 m"
            ),
            "routing_entry_capacity": t("Up to 256K IPv4 FIB entries and 80K IPv6 FIB entries"),
            "lag_group_capacity": t("1024 LAGs maximum; up to 256 links per LAG"),
            "l2_features": t(
                "Access/trunk/hybrid VLAN ports; QinQ; LACP; Smart Link; IGMP snooping; "
                "M-LAG; VXLAN routing/bridging; BGP-EVPN"
            ),
            "stp_features": t("STP; RSTP; MSTP; VBST; BPDU protection"),
            "ospf_support": b(True),
            "rip_support": b(True),
            "acl_security": t(
                "ACL/CAR; 802.1X; AAA/RADIUS/HWTACACS; IP/MAC/port/VLAN binding; "
                "port isolation/security; DoS/ARP/ICMP attack defense"
            ),
            "management_methods": t(
                "Console; Telnet; SSH; SNMPv1/v2/v3; FTP/TFTP; NETCONF; telemetry; "
                "iMaster NCE-Fabric; ZTP; Ansible"
            ),
            "sdn_support": b(True, "iMaster NCE-Fabric; OpenFlow; OPS open APIs; Ansible"),
            "redundant_power": b(True, "Redundant hot-swappable power modules can be configured"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and repair Huawei CloudEngine CE6863H-48S6CQ specifications."
    products = PRODUCTS
    document_version = "Official detailed datasheet, copyright 2025; accessed 2026-10-20"
    brand_name = "Huawei"
