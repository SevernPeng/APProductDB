from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


CURRENT_URL = "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9500-series-switches/nb-06-cat9500-ser-data-sheet-cte-en.html"
HARDWARE_URL = "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9500/hardware/install/b_catalyst_9500_hig/9500_product-overview.html"


COMMON = {
    "acl_security": t(
        "IPv4/IPv6/MAC ACLs, object-group ACLs, Cisco TrustSec/SGT, 802.1X, DHCP snooping, "
        "Dynamic ARP Inspection, IP Source Guard, port security and control-plane policing"
    ),
    "configuration_rollback": b(True, "Cisco IOS XE configuration archive and rollback are supported"),
    "console_interfaces": t("1 x RJ-45 console and 1 x USB Mini-B console"),
    "cpu": t("Intel 2.4 GHz x86 CPU"),
    "dhcp_features": t("DHCP server/relay, DHCP snooping and DHCPv6 guard"),
    "dram_memory": t("16 GB"),
    "fanless": b(False, "Field-replaceable variable-speed fans are fitted"),
    "flash_memory": t("16 GB"),
    "hot_patching": b(True, "Cisco IOS XE Software Maintenance Upgrade and critical bug patching"),
    "l2_features": t(
        "802.1Q VLANs, LACP/EtherChannel, LLDP/CDP, IGMP/MLD snooping, Private VLAN, "
        "REP, Flex Link and multichassis EtherChannel with StackWise Virtual"
    ),
    "l3_features": t(
        "IPv4/IPv6 static routing, RIPv2/RIPng, OSPFv2/v3, EIGRP/EIGRPv6, IS-IS, BGP, "
        "PBR, VRF, ECMP, PIM, MPLS L2/L3 VPN and EVPN-VXLAN; license dependent"
    ),
    "macsec_support": b(True, "Line-rate IEEE 802.1AE MACsec with 256-bit AES-GCM"),
    "management_interfaces": t("1 x dedicated RJ-45 Ethernet management port"),
    "management_methods": t(
        "Cisco IOS XE CLI/WebUI, SNMP, NETCONF/RESTCONF/gNMI with YANG, streaming telemetry, "
        "Cisco Catalyst Center, or Meraki dashboard cloud monitoring"
    ),
    "mld_snooping": b(True, "IGMP and MLD snooping are supported"),
    "mpls_support": b(True, "MPLS L3 VPN, EoMPLS, VPLS, MPLS over GRE and MPLS-TE; license dependent"),
    "multicast_routing": b(True, "PIM-SM, PIM-SSM and bidirectional PIM are supported"),
    "netconf_support": b(True, "NETCONF, RESTCONF, gNMI/gNOI and YANG models are supported"),
    "operating_temperature_c": t("0 to 40 °C up to 3,000 m; operation up to 45 °C at 1,800 m"),
    "ospf_support": b(True, "OSPFv2 and OSPFv3 are supported"),
    "packet_buffer_mb": n(36, "Up to 36 MB unified packet buffer per ASIC"),
    "pbr_support": b(True, "Policy-based routing is supported; scale depends on SDM template"),
    "ptp_support": b(True, "IEEE 1588v2 Precision Time Protocol with sub-microsecond accuracy"),
    "qos_support": t("MQC, strict-priority and class/color-aware queuing, policing, shaping and two-level hierarchical QoS"),
    "redundant_power": b(True, "Two hot-swappable power-supply bays support 1+1 redundancy"),
    "rip_support": b(True, "RIPv2 and RIPng are supported"),
    "sdn_support": b(True, "Cisco SD-Access control-plane/border roles, VXLAN and Catalyst Center automation"),
    "secure_boot": b(True, "Secure Boot, image signing and Cisco Trust Anchor module"),
    "stacking": t("Cisco StackWise Virtual (two physical switches operate as one logical system)"),
    "stacking_units": n(2, "StackWise Virtual pairs two switches"),
    "stp_features": t("PVST+, Rapid PVST+ and MST"),
    "switch_usb_interfaces": t("1 x USB 3.0 host port"),
    "vlan_count": n(4094, "Maximum VLAN IDs"),
    "vrrp_support": b(True, "VRRP is supported by Cisco IOS XE"),
    "vxlan_support": b(True, "BGP EVPN VXLAN and Cisco SD-Access VXLAN; license dependent"),
}


HIGH_PERFORMANCE = {
    **COMMON,
    "arp_entry_capacity": t("Up to 90,000 IPv4 host/direct-route and ARP entries; table maximum"),
    "fan_design": t("Field-replaceable variable-speed fan trays; front-to-back airflow and one-fan-failure tolerance"),
    "igmp_group_capacity": t("2,000 IGMP/MLD snooping entries in standard SDM templates"),
    "ip_interface_capacity": t("Up to 80,000 hardware adjacencies for VLAN/SVI interfaces with the distribution SDM template"),
    "jumbo_frame_bytes": n(9216, "Maximum jumbo frame size"),
    "mac_address_table": t("Up to 82,000 MAC addresses with the distribution SDM template"),
    "routing_entry_capacity": t(
        "Up to 256,000 IPv4 or IPv6 indirect + direct routes and up to 90,000 host routes; "
        "actual allocation depends on SDM template and prefix mix"
    ),
}


LEGACY = {
    **COMMON,
    "arp_entry_capacity": t("Up to 80,000 IPv4 host routes with SD-Access template; template dependent"),
    "fan_design": t("5 x field-replaceable variable-speed fans; front-to-back airflow and one-fan-failure tolerance"),
    "igmp_group_capacity": t("16,000 IGMP/MLD snooping entries"),
    "ip_interface_capacity": t("Up to approximately 32,000 hardware adjacencies across routed ports and VLAN/SVI interfaces"),
    "jumbo_frame_bytes": n(9198, "Maximum jumbo frame size for first-generation Catalyst 9500 models"),
    "mac_address_table": t("Up to 64,000 MAC addresses with the distribution SDM template"),
    "routing_entry_capacity": t(
        "Up to 64,000 IPv4 / 32,000 IPv6 LPM routes; host routes up to 80,000 IPv4 / 40,000 IPv6 "
        "with the SD-Access template"
    ),
}


def values(base, **kwargs):
    return {**base, **kwargs}


PRODUCTS = {
    "C9500-24Y4C": {
        "url": CURRENT_URL,
        "page": "Tables 1, 3, 9, 14, 16, 18 and 24; current 2026 data sheet",
        "title": "Cisco Catalyst 9500 Series Switches Data Sheet (current 2026 edition)",
        "values": values(
            HIGH_PERFORMANCE,
            dimensions_mm=t("444.5 x 457.2 x 43.9 mm (W x D x H), 1 RU"),
            ethernet_interfaces=t("24 x 1/10/25GbE SFP28 ports"),
            fan_design=t("4 x C9K-T1 field-replaceable variable-speed fan trays; front-to-back airflow"),
            packet_forwarding_rate_mpps=n(1000, "Up to 1 Bpps forwarding rate"),
            power_supply=t("1 x 650 W AC PSU supplied; two bays support 1+1 redundancy; 930 W DC option"),
            stacking_ports=t("Any 1/10/25GbE downlink or 40/100GbE fixed uplink can be used for StackWise Virtual"),
            switching_capacity_gbps=n(2000, "Up to 2.0 Tbps switching capacity"),
            uplink_interfaces=t("4 x 40/100GbE QSFP28 fixed uplink ports"),
        ),
    },
    "C9500-32C": {
        "url": CURRENT_URL,
        "page": "Tables 1, 3, 9, 14, 16, 18 and 24; current 2026 data sheet",
        "title": "Cisco Catalyst 9500 Series Switches Data Sheet (current 2026 edition)",
        "values": values(
            HIGH_PERFORMANCE,
            dimensions_mm=t("444.5 x 538.5 x 43.9 mm (W x D x H), 1 RU"),
            ethernet_interfaces=t("32 x 40/100GbE QSFP28 ports; up to 96 x 10GbE or 96 x 25GbE with breakout"),
            fan_design=t("5 x C9K-T2 field-replaceable variable-speed fan trays; front-to-back airflow"),
            packet_forwarding_rate_mpps=n(2000, "Up to 2 Bpps forwarding rate"),
            power_supply=t("1 x 1600 W AC PSU supplied; two bays support 1+1 redundancy; 1600 W DC option"),
            stacking_ports=t("Ports 1-16 at 40/100GbE can be used as StackWise Virtual links"),
            switching_capacity_gbps=n(6400, "Up to 6.4 Tbps switching capacity"),
            uplink_interfaces=t("32 x 40/100GbE QSFP28 ports are available for data or uplink use"),
        ),
    },
    "C9500-40X-2Q": {
        "url": HARDWARE_URL,
        "page": "Switch Models, Network Modules and Physical Specifications; current hardware guide plus current C9500 data sheet",
        "title": "Cisco Catalyst 9500 Hardware Installation Guide: C9500-40X-2Q bundle",
        "values": values(
            LEGACY,
            dimensions_mm=t("445 x 546.6 x 43.9 mm (W x D x H), 1 RU"),
            ethernet_interfaces=t("40 x 1/10GbE SFP/SFP+ ports"),
            packet_forwarding_rate_mpps=n(720, "Up to 720 Mpps forwarding rate"),
            power_supply=t("1 x 950 W AC PSU supplied; two bays support 1+1 redundancy; 950 W DC option"),
            stacking_ports=t("2 x 40GbE QSFP+ module ports can be used for StackWise Virtual links"),
            switching_capacity_gbps=n(960, "Up to 960 Gbps with the two-port 40GbE network module"),
            uplink_interfaces=t("C9500-NM-2Q module with 2 x 40GbE QSFP+ uplinks; each supports 4 x 10GbE breakout"),
        ),
    },
    "C9500-48Y4C": {
        "url": CURRENT_URL,
        "page": "Tables 1, 3, 9, 14, 16, 18 and 24; current 2026 data sheet",
        "title": "Cisco Catalyst 9500 Series Switches Data Sheet (current 2026 edition)",
        "values": values(
            HIGH_PERFORMANCE,
            dimensions_mm=t("444.5 x 457.2 x 43.9 mm (W x D x H), 1 RU"),
            ethernet_interfaces=t("48 x 1/10/25GbE SFP28 ports"),
            fan_design=t("4 x C9K-T1 field-replaceable variable-speed fan trays; front-to-back airflow"),
            packet_forwarding_rate_mpps=n(1000, "Up to 1 Bpps forwarding rate"),
            power_supply=t("1 x 650 W AC PSU supplied; two bays support 1+1 redundancy; 930 W DC option"),
            stacking_ports=t("Any 1/10/25GbE downlink or 40/100GbE fixed uplink can be used for StackWise Virtual"),
            switching_capacity_gbps=n(3200, "Up to 3.2 Tbps switching capacity"),
            uplink_interfaces=t("4 x 40/100GbE QSFP28 fixed uplink ports"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Catalyst C9500 core-switch specifications."
    products = PRODUCTS
    document_version = "Cisco Catalyst 9500 current data sheet and hardware guide; accessed 2026-10-16"
    brand_name = "Cisco"
