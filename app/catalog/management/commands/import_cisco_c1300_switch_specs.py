from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL = "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1300-series-switches/nb-06-cat1300-ser-data-sheet-cte-en.html"


COMMON = {
    "acl_security": t(
        "IPv4/IPv6/MAC ACLs; 802.1X, RADIUS/TACACS+, DHCP snooping, IP Source Guard, Dynamic ARP Inspection, "
        "port security, BPDU/Root/Loop guards and private VLANs"
    ),
    "dhcp_features": t("IPv4 DHCP server, Layer 2/Layer 3 DHCP relay, DHCP snooping and DHCP options"),
    "ip_interface_capacity": t("128 IP interfaces"),
    "jumbo_frame_bytes": n(9000, "Maximum jumbo frame size"),
    "l2_features": t(
        "802.1Q VLAN, private/voice/guest VLAN, Q-in-Q, GVRP, IGMP v1/v2/v3 snooping, MVR, UDLD and LACP"
    ),
    "l3_features": t("Wire-speed IPv4/IPv6 routing, static/dynamic routes, RIP v2, PBR, CIDR and routed interfaces"),
    "lag_group_capacity": t("8 LAG groups, up to 8 ports per group; IEEE 802.3ad LACP"),
    "management_methods": t(
        "Web GUI, CLI, SSH, HTTPS, SNMP, RMON, sFlow, syslog, Cisco Business Dashboard and mobile app"
    ),
    "multicast_routing": b(
        True,
        "IGMP proxy and MLD proxy provide multicast forwarding from group-membership information without requiring a multicast routing protocol",
    ),
    "operating_temperature_c": t("-5 to 50 °C"),
    "ospf_support": b(False, "OSPF v2/v3 is supported only by Catalyst 1300X SKUs, not these C1300 models"),
    "pbr_support": b(True, "Policy-based routing for IPv4/IPv6 ACL-selected traffic"),
    "rip_support": b(True, "RIP v2 dynamic routing"),
    "routing_entry_capacity": t("990 combined dynamic and static IPv4 routes"),
    "stacking": t("Hardware front-panel stacking with active/standby control, ring or chain topology and cross-stack LAG"),
    "stacking_bandwidth_gbps": n(40, "Up to four 10GbE SFP+ front-panel stack links"),
    "stacking_units": n(8, "Maximum switches per hardware stack"),
    "stp_features": t("802.1D STP, 802.1w RSTP, 802.1s MSTP (16 instances), PVST+ and Rapid PVST+ (126 instances)"),
    "vlan_count": n(4094, "Supports VLAN IDs up to 4094; VLANs 4078-4094 are reserved for internal use"),
}


def values(**kwargs):
    return {**COMMON, **kwargs}


PRODUCTS = {
    "C1300-24T-4X": {
        "url": URL,
        "page": "Product specifications and environmental tables; accessed 2026-10-16",
        "title": "Cisco Catalyst 1300 and 1300X Series Switches Data Sheet (2026)",
        "values": values(
            dimensions_mm=t("444.3 x 240 x 43.94 mm (W x D x H)"),
            ethernet_interfaces=t("24 x 10/100/1000BASE-T RJ-45"),
            fan_design=t("Fanless"),
            fanless=b(True, "Published fan table lists this model as fanless"),
            max_power_consumption_w=n(22.4, "Worst-case system power consumption at 220 V"),
            packet_forwarding_rate_mpps=n(95.23, "Forwarding capacity at 64-byte packets"),
            power_supply=t("Internal universal 100-240 V AC, 50-60 Hz"),
            switching_capacity_gbps=n(128, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 10GbE SFP+"),
        ),
    },
    "C1300-24FP-4X": {
        "url": URL,
        "page": "Product specifications and environmental tables; accessed 2026-10-16",
        "title": "Cisco Catalyst 1300 and 1300X Series Switches Data Sheet (2026)",
        "values": values(
            dimensions_mm=t("444.3 x 350 x 43.94 mm (W x D x H)"),
            ethernet_interfaces=t("24 x 10/100/1000BASE-T PoE+ RJ-45"),
            fan_design=t("1 internal fan; 39 dBA at 25 °C"),
            fanless=b(False, "Published fan table lists one fan"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ power per port"),
            max_power_consumption_w=n(454.2, "Worst-case total consumption with PoE load at 110 V"),
            packet_forwarding_rate_mpps=n(95.23, "Forwarding capacity at 64-byte packets"),
            poe_budget_w=n(375, "Published power dedicated to PoE"),
            poe_configuration=t("24 x PoE+ ports, 375 W total PoE budget"),
            poe_ports=n(24, "All 24 copper access ports support PoE"),
            poe_standard=t("IEEE 802.3af PoE and IEEE 802.3at PoE+"),
            power_supply=t("Internal universal 100-240 V AC, 50-60 Hz"),
            switching_capacity_gbps=n(128, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 10GbE SFP+"),
        ),
    },
    "C1300-48T-4X": {
        "url": URL,
        "page": "Product specifications and environmental tables; accessed 2026-10-16",
        "title": "Cisco Catalyst 1300 and 1300X Series Switches Data Sheet (2026)",
        "values": values(
            dimensions_mm=t("444.3 x 288 x 43.94 mm (W x D x H)"),
            ethernet_interfaces=t("48 x 10/100/1000BASE-T RJ-45"),
            fan_design=t("1 internal fan; 29.7 dBA at 25 °C"),
            fanless=b(False, "Published fan table lists one fan"),
            max_power_consumption_w=n(40.01, "Worst-case system power consumption at 110 V"),
            packet_forwarding_rate_mpps=n(130.94, "Forwarding capacity at 64-byte packets"),
            power_supply=t("Internal universal 100-240 V AC, 50-60 Hz"),
            switching_capacity_gbps=n(176, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 10GbE SFP+"),
        ),
    },
    "C1300-48FP-4X": {
        "url": URL,
        "page": "Product specifications and environmental tables; accessed 2026-10-16",
        "title": "Cisco Catalyst 1300 and 1300X Series Switches Data Sheet (2026)",
        "values": values(
            dimensions_mm=t("444.3 x 350 x 43.94 mm (W x D x H)"),
            ethernet_interfaces=t("48 x 10/100/1000BASE-T PoE+ RJ-45"),
            fan_design=t("1 internal fan; 48.7 dBA at 25 °C"),
            fanless=b(False, "Published fan table lists one fan"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ power per port"),
            max_power_consumption_w=n(874.52, "Worst-case total consumption with PoE load at 110 V"),
            packet_forwarding_rate_mpps=n(130.94, "Forwarding capacity at 64-byte packets"),
            poe_budget_w=n(740, "Published power dedicated to PoE"),
            poe_configuration=t("48 x PoE+ ports, 740 W total PoE budget"),
            poe_ports=n(48, "All 48 copper access ports support PoE"),
            poe_standard=t("IEEE 802.3af PoE and IEEE 802.3at PoE+"),
            power_supply=t("Internal universal 100-240 V AC, 50-60 Hz"),
            switching_capacity_gbps=n(176, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 10GbE SFP+"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Catalyst 1300 24/48-port 4X switch specifications."
    products = PRODUCTS
    document_version = "Cisco Catalyst 1300/1300X data sheet, current 2026 edition; accessed 2026-10-16"
    brand_name = "Cisco"
