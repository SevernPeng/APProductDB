from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DXS1210_DS = "https://www2.dlink.com/en/-/media/product-pages/dxs/1210-series/dxs121028tsa1datasheetv103ww.pdf"


COMMON = {
    "jumbo_frame_bytes": n(12288, "Jumbo Frame: Up to 12,288 Bytes"),
    "vlan_count": n(
        4096,
        "4K VLAN Groups; configurable VID 1-4094",
    ),
    "operating_temperature_c": t(
        "-5 to 50 °C",
        "Operating temperature: -5 to 50 °C (23 to 122 °F)",
    ),
    "dimensions_mm": t(
        "441 x 209.5 x 44 mm (L x W x H)",
        "Dimensions (L x W x H): 441 x 209.5 x 44 mm",
    ),
    "power_supply": t("Internal 100-240 V AC", "AC input: 100 to 240 VAC"),
    "management_methods": t(
        "Web GUI, D-Link Network Assistant, full CLI via console or Telnet, SNMP v1/v2c/v3, RMON v1/v2",
        "Management: Web-based GUI, D-Link Network Assistant Utility, full CLI, Telnet, SNMP v1/v2c/v3 and RMON v1/v2",
    ),
    "stp_features": t(
        "IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP",
        "Spanning Tree Protocol: 802.1D STP, 802.1w RSTP, 802.1s MSTP",
    ),
    "l2_features": t(
        "IGMP v1/v2/v3 and MLD v1/v2 snooping, LLDP/LLDP-MED, 802.3x flow control, port mirroring, 802.3ad link aggregation, loopback detection, 4K VLAN groups and 12,288-byte jumbo frames",
        "L2 features include IGMP/MLD snooping, LLDP/LLDP-MED, STP/RSTP/MSTP, flow control, port mirroring, 802.3ad LAG, jumbo frame and loopback detection",
    ),
    "acl_security": t(
        "IPv4, IPv6, MAC and VLAN ACLs; up to 1,536 ingress and 1,024 egress entries; 802.1X, DHCP snooping, IP-MAC-port binding, DAI, source guard, RA guard, SSH and TLS",
        "ACL: IPv4/MAC/IPv6/VLAN based; maximum 1536 ingress and 1024 egress entries. Security includes 802.1X, DHCP snooping, IP-MAC-port binding, DAI, source guards, SSH and SSL/TLS.",
    ),
}


PRODUCTS = {
    "DXS-1210-28T": {
        "url": DXS1210_DS,
        "page": "pp. 1-5, A1 v1.03 (WW) performance, physical and software specifications",
        "title": "D-Link DXS-1210 Series Data Sheet A1 v1.03 (WW)",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(680, "Switching capacity: 680 Gbps"),
            "packet_forwarding_rate_mpps": n(505.92, "Maximum packet forwarding rate: 505.92 Mpps"),
            "max_power_consumption_w": n(
                90,
                "Maximum power consumption: 90 W at 100 V/60 Hz; 87.3 W at 240 V/60 Hz",
            ),
        },
    },
    "DXS-1210-28S": {
        "url": DXS1210_DS,
        "page": "pp. 1-5, A1 v1.03 (WW) performance, physical and software specifications",
        "title": "D-Link DXS-1210 Series Data Sheet A1 v1.03 (WW)",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(560, "Switching capacity: 560 Gbps"),
            "packet_forwarding_rate_mpps": n(416.64, "Maximum packet forwarding rate: 416.64 Mpps"),
            "max_power_consumption_w": n(
                87.7,
                "Maximum power consumption: 87.7 W at 100 V/60 Hz; 85.7 W at 240 V/60 Hz",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current D-Link DXS-1210-28T/28S performance, 12K jumbo-frame and 4K VLAN specifications."
    products = PRODUCTS
    document_version = "A1 v1.03 (WW), ©2025 D-Link; accessed 2026-10-22"
    brand_name = "D-Link"

