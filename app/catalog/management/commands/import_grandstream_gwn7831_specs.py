from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


DATASHEET = (
    "https://www.grandstream.com/hubfs/Product_Documentation/"
    "GWN7830%20Series/Datasheet_GWN7830_Series_English.pdf"
)


PRODUCTS = {
    "GWN7831": {
        "url": DATASHEET,
        "page": "GWN7830 Series datasheet, pages 2-3, version 5.2024.01",
        "title": "Grandstream GWN7830 Series official English datasheet",
        "values": {
            "ethernet_interfaces": t(
                "20 x 1G SFP ports; 4 x 1G RJ45/SFP combo ports; 4 x 10G SFP+ ports"
            ),
            "uplink_interfaces": t("4 x 10G SFP+ ports; DAC cables up to 5 m supported"),
            "console_interfaces": t("1 x console port"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.232),
            "packet_buffer_mb": n(12),
            "mac_address_table": t("16K MAC addresses"),
            "jumbo_frame_bytes": n(9216),
            "vlan_count": n(4096),
            "ip_interface_capacity": t("16 VLAN interfaces"),
            "arp_entry_capacity": t("1K ARP/NDP entries"),
            "lag_group_capacity": t("32 link aggregation groups"),
            "l2_features": t(
                "4K VLANs; port-, MAC- and protocol-based VLAN; private VLAN; "
                "voice VLAN; 32 LAG groups; GVRP and ERPS pending"
            ),
            "stp_features": t("32 instances of STP/RSTP/MSTP/PVST+/RPVST+"),
            "routing_entry_capacity": t("512 IPv4 routes; 128 IPv6 routes"),
            "l3_features": t(
                "IPv4/IPv6 static routing; RIP/RIPng; OSPF/OSPFv3; BGP; "
                "routing policy; policy routing and VRRP pending"
            ),
            "rip_support": b(True),
            "ospf_support": b(True),
            "pbr_support": b(False, "Policy routing pending"),
            "vrrp_support": b(False, "VRRP pending"),
            "multicast_routing": b(True, "IPv4/IPv6 multicast features published"),
            "mld_snooping": b(True),
            "igmp_group_capacity": t("256 IGMP snooping groups; 256 MLD snooping groups"),
            "dhcp_features": t(
                "DHCP server and relay; DHCP options 82, 60, 160 and 43; "
                "DHCP/DHCPv6 snooping"
            ),
            "acl_security": t(
                "2K Ethernet/IPv4/IPv6 ACL; 802.1X and MAC authentication; "
                "RADIUS/TACACS+; ARP inspection; IP source guard; DoS protection"
            ),
            "management_interfaces": t("Web GUI; CLI via console, Telnet or SSH; SNMP v1/v2c/v3"),
            "management_methods": t(
                "Local Web UI and CLI; GDMS Networking; GWN Manager; GWN router; "
                "SNMP, RMON, LLDP/LLDP-MED and syslog"
            ),
            "configuration_rollback": b(True, "Configuration backup and restore supported"),
            "stacking": t("Hardware stacking; up to four switches managed as one logical device"),
            "stacking_units": n(4),
            "power_supply": t("Integrated 60 W power supply; optional external 12 V / 60 W RPS"),
            "redundant_power": b(True),
            "fan_design": t("2 internal variable-speed fans"),
            "fanless": b(False),
            "operating_temperature_c": t("0 to 45 °C"),
            "dimensions_mm": t("440 x 200 x 44 mm"),
            "erps_support": b(False, "ERPS pending"),
            "ptp_support": b(True, "IEEE 1588 PTP transparent clock"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified Grandstream GWN7831 managed-switch specifications."
    products = PRODUCTS
    document_version = (
        "Grandstream GWN7830 Series official English datasheet 5.2024.01; "
        "accessed 2026-10-16"
    )
    brand_name = "Grandstream"
