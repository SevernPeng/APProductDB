from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL = "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-9200-series-switches/nb-06-cat9200-ser-data-sheet-cte-en.html"


COMMON = {
    "acl_security": t(
        "IPv4/IPv6/MAC ACLs, 802.1X, Cisco TrustSec/SGT, DHCP snooping, Dynamic ARP Inspection, "
        "IP Source Guard, port security and control-plane protection"
    ),
    "dimensions_mm": t("445 x 288 x 44 mm (W x D x H), excluding protrusions"),
    "ethernet_interfaces": t("10/100/1000BASE-T access ports"),
    "fan_design": t("Two fixed redundant fans"),
    "fanless": b(False, "Catalyst 9200L models use fixed redundant fans"),
    "ip_interface_capacity": t("512 switched virtual interfaces (SVIs)"),
    "jumbo_frame_bytes": n(9198, "Maximum jumbo frame size"),
    "l2_features": t("802.1Q VLANs, LACP/EtherChannel, LLDP, CDP, IGMP/MLD snooping, REP and Flex Link"),
    "l3_features": t("Static routing, RIPv1/v2/RIPng, OSPF/OSPFv3, EIGRP, IS-IS and routed access; license dependent"),
    "mac_address_table": t("16,000 MAC addresses"),
    "management_methods": t(
        "Cisco IOS XE CLI/WebUI, NETCONF/RESTCONF/YANG, SNMP, telemetry, Cisco Catalyst Center, "
        "or Meraki dashboard cloud management"
    ),
    "multicast_routing": b(True, "PIM sparse mode and source-specific multicast are supported"),
    "netconf_support": b(True, "Cisco IOS XE supports NETCONF/RESTCONF with YANG models"),
    "operating_temperature_c": t(
        "-5 to 45 °C normal up to 1500 m; -5 to 40 °C up to 3000 m; short-term up to 50 °C"
    ),
    "ospf_support": b(True, "OSPF/OSPFv3; feature scale depends on license tier"),
    "redundant_power": b(True, "Two field-replaceable power-supply slots; second PSU can provide redundancy or more PoE power"),
    "rip_support": b(True, "RIPv1, RIPv2 and RIPng are supported"),
    "routing_entry_capacity": t("11,000 total IPv4 routes (8,000 direct and 3,000 indirect)"),
    "sdn_support": b(True, "Cisco SD-Access is supported with one virtual network; Catalyst Center automation and assurance"),
    "stacking": t("Cisco StackWise-80 backplane stacking"),
    "stacking_bandwidth_gbps": n(80, "StackWise-80 stacking bandwidth"),
    "stacking_units": n(8, "Maximum members per stack"),
    "stp_features": t("PVST+, Rapid PVST+ and MST; up to 128 PVST instances"),
    "uplink_interfaces": t("4 x fixed 1/10GbE SFP+ uplinks"),
    "vlan_count": n(4094, "Maximum VLAN IDs"),
}


def values(**kwargs):
    return {**COMMON, **kwargs}


PRODUCTS = {
    "C9200L-24T-4X": {
        "url": URL,
        "page": "Tables 2, 5, 8-12 and 17; current 2026 data sheet",
        "title": "Cisco Catalyst 9200 Series Switches Data Sheet (updated 2026)",
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T data ports"),
            max_power_consumption_w=n(38.6, "Maximum measured standalone consumption at 115 VAC and full-port traffic"),
            packet_forwarding_rate_mpps=n(95.23, "Standalone forwarding rate"),
            power_supply=t("1 x PWR-C5-125WAC supplied; second 125 W AC PSU optional"),
            switching_capacity_gbps=n(128, "Standalone switching capacity"),
        ),
    },
    "C9200L-24P-4X": {
        "url": URL,
        "page": "Tables 2, 4, 5, 8-12 and 17; current 2026 data sheet",
        "title": "Cisco Catalyst 9200 Series Switches Data Sheet (updated 2026)",
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T full PoE+ ports"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(445.35, "Maximum measured consumption at 115 VAC with 100% PoE test load"),
            packet_forwarding_rate_mpps=n(95.23, "Standalone forwarding rate"),
            poe_budget_w=n(740, "Maximum PoE budget with two PWR-C5-600WAC supplies; 370 W with one"),
            poe_configuration=t("24 full PoE+ ports; 370 W with one 600 W PSU or 740 W with two"),
            poe_ports=n(24, "All access ports support PoE+"),
            poe_standard=t("IEEE 802.3af PoE and IEEE 802.3at PoE+; Perpetual PoE and Fast PoE"),
            power_supply=t("1 x PWR-C5-600WAC supplied; second 600 W AC PSU optional"),
            switching_capacity_gbps=n(128, "Standalone switching capacity"),
        ),
    },
    "C9200L-48T-4X": {
        "url": URL,
        "page": "Tables 2, 5, 8-12 and 17; current 2026 data sheet",
        "title": "Cisco Catalyst 9200 Series Switches Data Sheet (updated 2026)",
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T data ports"),
            max_power_consumption_w=n(53.67, "Maximum measured standalone consumption at 230 VAC and full-port traffic"),
            packet_forwarding_rate_mpps=n(130.95, "Standalone forwarding rate"),
            power_supply=t("1 x PWR-C5-125WAC supplied; second 125 W AC PSU optional"),
            switching_capacity_gbps=n(176, "Standalone switching capacity"),
        ),
    },
    "C9200L-48P-4X": {
        "url": URL,
        "page": "Tables 2, 4, 5, 8-12 and 17; current 2026 data sheet",
        "title": "Cisco Catalyst 9200 Series Switches Data Sheet (updated 2026)",
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T full PoE+ ports"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(872.6, "Maximum measured consumption at 115 VAC with 100% PoE test load"),
            packet_forwarding_rate_mpps=n(130.95, "Standalone forwarding rate"),
            poe_budget_w=n(1440, "Maximum PoE budget with two PWR-C5-1KWAC supplies; 740 W with one"),
            poe_configuration=t("48 full PoE+ ports; 740 W with one 1000 W PSU or 1440 W with two"),
            poe_ports=n(48, "All access ports support PoE+"),
            poe_standard=t("IEEE 802.3af PoE and IEEE 802.3at PoE+; Perpetual PoE and Fast PoE"),
            power_supply=t("1 x PWR-C5-1KWAC supplied; second 1000 W AC PSU optional"),
            switching_capacity_gbps=n(176, "Standalone switching capacity"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Catalyst C9200L 24/48-port 4X switch specifications."
    products = PRODUCTS
    document_version = "Cisco Catalyst 9200 data sheet, current 2026 edition; accessed 2026-10-16"
    brand_name = "Cisco"
