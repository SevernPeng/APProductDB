from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


DS = "https://www.dlink.com/en/-/media/business_products/dqs/dqs-5000-32q/datasheet/5000seriesa1datasheetv300ww.pdf"


COMMON = {
    "jumbo_frame_bytes": n(9216, "Jumbo frame: Up to 9 Kb"),
    "vlan_count": n(4096, "Maximum 4K VLAN groups; VLAN IDs 1-4093"),
    "operating_temperature_c": t("0 to 45 °C", "Operating temperature: 0 to 45 ºC (32 to 113 ºF)"),
    "l2_features": t(
        "802.3ad link aggregation (64 groups, 32 ports/group); 802.3x flow control; port, flow and VLAN mirroring; RSPAN; loopback detection; IGMP v1/v2/v3 and MLD v1/v2 snooping",
        "D-Link OS L2 features include 802.3ad, flow control, port/flow/VLAN mirroring, RSPAN, LBD, IGMP snooping v1/v2/v3 and MLD snooping v1/v2",
    ),
    "stp_features": t(
        "IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP; BPDU Filter/Guard, Loop Guard, TCN Guard and Root Guard",
        "Spanning Tree Protocol: 802.1D STP, 802.1w RSTP, 802.1s MSTP; BPDU Filter/Guard, Loop Guard, TCN Guard, Root Guard",
    ),
    "acl_security": t(
        "MAC/IPv4/IPv6 ACLs with time-based ACL and CPU-interface filtering; up to 16K ingress and 16K egress ACL entries, 100 access control lists and 1K ACL rules; 802.1X, RADIUS, TACACS+, DHCP snooping, IP Source Guard and DAI",
        "ACL: maximum 16K ingress and 16K egress entries, 100 access control lists, 1K ACL rules; security and AAA include 802.1X, RADIUS, TACACS+, DHCP snooping, IP Source Guard and DAI",
    ),
    "management_methods": t(
        "Industry-standard CLI; Telnet; TFTP/FTP/SFTP; SNMP v1/v2c/v3; IPv4/IPv6 Syslog; RMON; LLDP/LLDP-MED; sFlow v5; DHCP auto-configuration and auto-image; ONIE",
        "D-Link OS management: CLI, Telnet, TFTP/FTP/SFTP, SNMP v1/v2c/v3, Syslog, RMON, LLDP/LLDP-MED, sFlow v5 and DHCP auto-configuration; switch is preloaded with ONIE",
    ),
    "ip_interface_capacity": t("128 IP interfaces", "IP interfaces: Supports 128 IP interfaces"),
    "routing_entry_capacity": t(
        "12K shared IPv4/IPv6 hardware routing entries; 20K shared IPv4/IPv6 hardware L3 forwarding entries; 64 IPv4 and 64 IPv6 static routes",
        "Supports 12K hardware routing entries and 20K hardware L3 forwarding entries shared by IPv4/IPv6; maximum 64 IPv4 and 64 IPv6 static routes",
    ),
    "ospf_support": b(True, "OSPF v2/v3 with Stub/NSSA area, passive interface, authentication, ECMP, graceful restart and BFD"),
    "pbr_support": b(True, "Policy-based Route (PBR)"),
    "dimensions_mm": t("440 x 406 x 44 mm", "Dimensions (W x D x H): 440 x 406 x 44 mm"),
    "power_supply": t(
        "Two hot-swappable AC or DC power modules; 1+1 redundancy and load sharing",
        "Two AC/DC hot-swappable power modules for 1+1 redundancy and load sharing",
    ),
    "fan_design": t(
        "4 modular hot-swappable fans; N+1 redundancy; front-to-back or back-to-front airflow",
        "4 fans; modular N+1 hot-swappable fan design; front-to-back and back-to-front airflow options",
    ),
}


PRODUCTS = {
    "DQS-5000-32Q28": {
        "url": DS,
        "page": "pp. 4-6, DQS-5000-32Q28 hardware table and D-Link OS feature tables",
        "title": "D-Link 5000 Series Data Center Switches Data Sheet v3.00 WW",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(6400, "Switching capacity: 6.4 Tbps"),
            "packet_forwarding_rate_mpps": n(2980, "Maximum forwarding rate: 2,980 Mpps (2.980 Bpps)"),
            "packet_buffer_mb": n(16, "Packet buffer memory: 16 MB"),
            "max_power_consumption_w": n(420, "Maximum power consumption: 420 W"),
        },
    },
    "DQS-5000-54SQ28": {
        "url": DS,
        "page": "pp. 4-6, DQS-5000-54SQ28 hardware table and D-Link OS feature tables",
        "title": "D-Link 5000 Series Data Center Switches Data Sheet v3.00 WW",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(3600, "Switching capacity: 3.6 Tbps"),
            "packet_forwarding_rate_mpps": n(2380, "Maximum forwarding rate: 2,380 Mpps (2.380 Bpps)"),
            "packet_buffer_mb": n(16, "Packet buffer memory: 16 MB"),
            "max_power_consumption_w": n(395, "Maximum power consumption: 395 W"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified D-Link DQS-5000-32Q28/54SQ28 hardware and D-Link OS specifications."
    products = PRODUCTS
    document_version = "A1 v3.00 WW; accessed 2026-10-22"
    brand_name = "D-Link"
