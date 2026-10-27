from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_250 = "https://www.cisco.com/c/en/us/products/collateral/switches/business-250-series-smart-switches/nb-06-bus250-smart-switch-ds-cte-en.html"
URL_350 = "https://www.cisco.com/c/en/us/products/collateral/switches/business-350-series-managed-switches/datasheet-c78-744156.html"


COMMON = {
    "acl_security": t(
        "IPv4/IPv6/MAC ACLs, 802.1X, DHCP snooping, IP Source Guard, Dynamic ARP Inspection, "
        "port security, RADIUS and denial-of-service prevention"
    ),
    "console_interfaces": t("1 x Cisco standard RJ-45 console port"),
    "cpu": t("800 MHz ARM"),
    "dhcp_features": t("DHCP client, server, Layer 2/Layer 3 relay, Option 82, DHCP snooping and DHCPv6 relay/guard"),
    "dram_memory": t("512 MB"),
    "ethernet_interfaces": t("10/100/1000BASE-T copper access ports"),
    "flash_memory": t("256 MB"),
    "jumbo_frame_bytes": n(9000, "Frames up to 9K bytes; default MTU is 2K bytes"),
    "l2_features": t(
        "802.1Q VLANs, LACP, LLDP/LLDP-MED, CDP, IGMP/MLD snooping, voice VLAN, private VLAN, "
        "GVRP/GARP, loopback detection and 802.3az Energy Efficient Ethernet"
    ),
    "management_methods": t(
        "Web GUI, text/menu CLI, SNMP, SSH, HTTPS, Cisco Business Dashboard/mobile app, "
        "single-IP management, RMON, syslog, TFTP/SCP and dual firmware images"
    ),
    "mld_snooping": b(True, "MLDv1/v2 snooping and MLD proxy are supported"),
    "operating_temperature_c": t("-5 to 50 °C"),
    "poe_standard": t("IEEE 802.3af PoE and IEEE 802.3at PoE+; Cisco legacy PoE"),
    "power_supply": t("Internal universal 100-240 VAC, 50/60 Hz power supply"),
    "stp_features": t("802.1D STP, 802.1w RSTP, 802.1s MSTP (8 instances), PVST+ and Rapid PVST+ (126 instances)"),
    "switch_usb_interfaces": t("1 x front-panel USB Type-A host port"),
}


COMMON_250 = {
    **COMMON,
    "ip_interface_capacity": t("Up to 16 IPv4 interfaces"),
    "l3_features": t("IPv4 static routing and inter-VLAN routing; up to 32 static routes and 16 IP interfaces"),
    "lag_group_capacity": t("Up to 4 LAGs, with up to 8 ports per LAG"),
    "mac_address_table": t("8,000 MAC addresses"),
    "packet_buffer_mb": n(1.5, "Dynamically shared packet buffer"),
    "routing_entry_capacity": t("Up to 32 IPv4 static routes"),
    "vlan_count": n(255, "Maximum simultaneously active VLANs"),
}


COMMON_350 = {
    **COMMON,
    "ip_interface_capacity": t("Up to 128 IPv4 interfaces"),
    "l3_features": t("IPv4/IPv6 static routing, RIPv2, policy-based routing, inter-VLAN routing and CIDR"),
    "lag_group_capacity": t("Up to 8 LAGs, with up to 8 ports per LAG"),
    "mac_address_table": t("16,000 MAC addresses"),
    "pbr_support": b(True, "IPv4/IPv6 ACL-based policy routing is supported"),
    "rip_support": b(True, "RIPv2 dynamic routing is supported"),
    "routing_entry_capacity": t("Up to 990 IPv4 static routes and 128 IP interfaces"),
    "stacking": t("True hardware stacking over 10GbE SFP+ links; ring or chain topology with active/standby control"),
    "stacking_units": n(4, "Up to four switches and 200 ports per stack"),
    "vlan_count": n(4094, "Maximum simultaneously active VLANs"),
}


def values(base, **kwargs):
    return {**base, **kwargs}


PRODUCTS = {
    "CBS250-16P-2G": {
        "url": URL_250,
        "page": "Table 1, performance, PoE, hardware and environmental sections; updated 2025-03-21",
        "title": "Cisco Business 250 Series Smart Switches Data Sheet",
        "values": values(
            COMMON_250,
            dimensions_mm=t("268 x 297 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("16 x 10/100/1000BASE-T PoE+ ports"),
            fan_design=t("Fanless passive cooling"),
            fanless=b(True, "Official acoustic table identifies this model as fanless"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(156.4, "Worst-case consumption at 110 VAC with PoE load"),
            packet_forwarding_rate_mpps=n(26.78, "Wire-speed forwarding rate for 64-byte packets"),
            poe_budget_w=n(120, "Power dedicated to PoE"),
            poe_configuration=t("16 PoE+ ports sharing a 120 W budget"),
            poe_ports=n(16, "All copper access ports support PoE+"),
            switching_capacity_gbps=n(36, "Nonblocking switching capacity"),
            uplink_interfaces=t("2 x 1GbE SFP uplink ports"),
        ),
    },
    "CBS250-24P-4G": {
        "url": URL_250,
        "page": "Table 1, performance, PoE, hardware and environmental sections; updated 2025-03-21",
        "title": "Cisco Business 250 Series Smart Switches Data Sheet",
        "values": values(
            COMMON_250,
            dimensions_mm=t("445 x 299 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("24 x 10/100/1000BASE-T PoE+ ports"),
            fan_design=t("Fanless passive cooling"),
            fanless=b(True, "Official acoustic table identifies this model as fanless"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(239.7, "Worst-case consumption at 110 VAC with PoE load"),
            packet_forwarding_rate_mpps=n(41.66, "Wire-speed forwarding rate for 64-byte packets"),
            poe_budget_w=n(195, "Power dedicated to PoE"),
            poe_configuration=t("24 PoE+ ports sharing a 195 W budget"),
            poe_ports=n(24, "All copper access ports support PoE+"),
            switching_capacity_gbps=n(56, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 1GbE SFP uplink ports"),
        ),
    },
    "CBS350-24T-4X": {
        "url": URL_350,
        "page": "Table 1, performance, stacking, hardware and environmental sections; updated 2024-05-25",
        "title": "Cisco Business 350 Series Managed Switches Data Sheet",
        "values": values(
            COMMON_350,
            dimensions_mm=t("445 x 240 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("24 x 10/100/1000BASE-T ports"),
            fan_design=t("Fanless passive cooling"),
            fanless=b(True, "Official acoustic table identifies this model as fanless"),
            max_power_consumption_w=n(27.54, "Worst-case system consumption at 110 VAC"),
            packet_buffer_mb=n(1.5, "Dynamically shared packet buffer"),
            packet_forwarding_rate_mpps=n(95.23, "Wire-speed forwarding rate for 64-byte packets"),
            switching_capacity_gbps=n(128, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 1/10GbE SFP+ uplinks; also used for hardware stacking"),
        ),
    },
    "CBS350-24FP-4X": {
        "url": URL_350,
        "page": "Table 1, performance, PoE, stacking, hardware and environmental sections; updated 2024-05-25",
        "title": "Cisco Business 350 Series Managed Switches Data Sheet",
        "values": values(
            COMMON_350,
            dimensions_mm=t("445 x 345 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("24 x 10/100/1000BASE-T PoE+ ports"),
            fan_design=t("1 x variable-speed fan; 34.8 dBA at 25 °C"),
            fanless=b(False, "Official acoustic table lists one fan"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(451.8, "Worst-case consumption at 110 VAC with PoE load"),
            packet_buffer_mb=n(1.5, "Dynamically shared packet buffer"),
            packet_forwarding_rate_mpps=n(95.23, "Wire-speed forwarding rate for 64-byte packets"),
            poe_budget_w=n(370, "Power dedicated to PoE"),
            poe_configuration=t("24 PoE+ ports sharing a 370 W budget"),
            poe_ports=n(24, "All copper access ports support PoE+"),
            switching_capacity_gbps=n(128, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 1/10GbE SFP+ uplinks; also used for hardware stacking"),
        ),
    },
    "CBS350-48T-4X": {
        "url": URL_350,
        "page": "Table 1, performance, stacking, hardware and environmental sections; updated 2024-05-25",
        "title": "Cisco Business 350 Series Managed Switches Data Sheet",
        "values": values(
            COMMON_350,
            dimensions_mm=t("445 x 288 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("48 x 10/100/1000BASE-T ports"),
            fan_design=t("1 x variable-speed fan; 29.7 dBA at 25 °C"),
            fanless=b(False, "Official acoustic table lists one fan"),
            max_power_consumption_w=n(51.01, "Worst-case system consumption at 110 VAC"),
            packet_buffer_mb=n(3, "Dynamically shared packet buffer"),
            packet_forwarding_rate_mpps=n(130.94, "Wire-speed forwarding rate for 64-byte packets"),
            switching_capacity_gbps=n(176, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 1/10GbE SFP+ uplinks; also used for hardware stacking"),
        ),
    },
    "CBS350-48FP-4X": {
        "url": URL_350,
        "page": "Table 1, performance, PoE, stacking, hardware and environmental sections; updated 2024-05-25",
        "title": "Cisco Business 350 Series Managed Switches Data Sheet",
        "values": values(
            COMMON_350,
            dimensions_mm=t("445 x 350 x 44 mm (W x D x H)"),
            ethernet_interfaces=t("48 x 10/100/1000BASE-T PoE+ ports"),
            fan_design=t("1 x variable-speed fan; 48.7 dBA at 25 °C"),
            fanless=b(False, "Official acoustic table lists one fan"),
            max_poe_per_port_w=n(30, "Maximum IEEE 802.3at PoE+ output per port"),
            max_power_consumption_w=n(889.35, "Worst-case consumption at 110 VAC with PoE load"),
            packet_buffer_mb=n(3, "Dynamically shared packet buffer"),
            packet_forwarding_rate_mpps=n(130.94, "Wire-speed forwarding rate for 64-byte packets"),
            poe_budget_w=n(740, "Power dedicated to PoE"),
            poe_configuration=t("48 PoE+ ports sharing a 740 W budget"),
            poe_ports=n(48, "All copper access ports support PoE+"),
            switching_capacity_gbps=n(176, "Nonblocking switching capacity"),
            uplink_interfaces=t("4 x 1/10GbE SFP+ uplinks; also used for hardware stacking"),
        ),
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Cisco Business 250 and 350 switch specifications."
    products = PRODUCTS
    document_version = "Cisco Business 250 (2025-03-21) and 350 (2024-05-25) data sheets; accessed 2026-10-16"
    brand_name = "Cisco"
