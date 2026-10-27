from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20CX%206300%20Switch%20Series%20"
    "QuickSpecs-a00073540enw.pdf?contentDisposition=attachment&form=false&hf=regular&"
    "id=a00073540enw.pdf&isFutureVersion=true&isLinearized=false&preview=false&ver=42"
)
TITLE = "HPE Aruba Networking CX 6300 Switch Series QuickSpecs, version 42"


PRODUCTS = {
    "6300M 24SFP+ 4SFP56 Switch (JL658A)": {
        "url": URL,
        "page": "pp. 75-77 technical specifications and pp. 2-14 standard features",
        "title": TITLE,
        "values": {
            "dimensions_mm": t("442 x 385 x 44 mm (W x D x H)"),
            "fanless": b(False, "Two hot-swappable fan trays are installed; each tray contains two fans"),
            "fan_design": t("2 field-replaceable hot-swappable fan trays; 2 fans per tray; front/side-to-back airflow"),
            "power_supply": t("2 hot-swappable PSU slots; minimum 1 JL085A 250W PSU ordered separately"),
            "redundant_power": b(True, "Two PSU slots support N+1 or N+N power redundancy"),
            "max_power_consumption_w": n(85, "Power consumption at 230 VAC and 100% traffic rate"),
            "operating_temperature_c": t(
                "0 to 45 °C up to 5,000 ft; 0 to 40 °C from 5,001 to 10,000 ft; short excursion to 55 °C"
            ),
            "cpu": t("Quad-core ARM Cortex-A72 at 1.8 GHz"),
            "dram_memory": t("8 GB DDR4"),
            "flash_memory": t("32 GB eMMC"),
            "packet_buffer_mb": n(8, "8 MB packet buffer memory"),
            "switching_capacity_gbps": n(880, "Model switching capacity"),
            "packet_forwarding_rate_mpps": n(654, "Model throughput capacity"),
            "jumbo_frame_bytes": n(9198, "Maximum frame size"),
            "mac_address_table": t("32,768 MAC addresses"),
            "arp_entry_capacity": t("49,152 IPv4 host/ARP entries"),
            "ip_interface_capacity": t("1,024 dual-stack switched virtual interfaces"),
            "igmp_group_capacity": t("4,096 IGMP groups"),
            "mld_snooping": b(True, "MLDv1/v2 and MLD snooping are supported; table capacity is 8,192 groups"),
            "vlan_count": n(4094, "IEEE 802.1Q support for 4,094 VLAN IDs"),
            "l2_features": t(
                "802.1Q VLAN; STP/RSTP/MSTP; LACP; IGMP/MLD snooping; QinQ; EVPN/VXLAN; port mirroring"
            ),
            "stp_features": t("IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP"),
            "lag_group_capacity": t("Up to 256 LAGs with up to eight links per LAG"),
            "dhcp_features": t("DHCP client, IPv4 DHCP server, DHCP relay, DHCP smart relay and DHCPv6 protection"),
            "routing_entry_capacity": t("61,000 IPv4 unicast routes; 61,000 IPv6 unicast routes"),
            "ospf_support": b(True, "OSPFv2 for IPv4 and OSPFv3 for IPv6 are supported"),
            "rip_support": b(True, "RIPv2 and RIPng are supported"),
            "pbr_support": b(True, "Policy-Based Routing is supported"),
            "sdn_support": b(True, "AOS-CX provides REST APIs, Python scripting and event-driven automation"),
            "hot_patching": b(True, "Hot-Patching and ISSU are supported for standalone and VSF deployments"),
            "m_lag_support": b(True, "Two-member VSX active-active clustering provides multi-chassis high availability"),
            "stacking": t("VSF front-plane stacking in chain or ring topology; optional two-member VSX cluster"),
            "stacking_units": n(10, "VSF supports up to 10 members"),
            "stacking_bandwidth_gbps": n(200, "200 Gbps stacking bandwidth; 400 Gbps full duplex"),
            "management_methods": t(
                "AOS-CX CLI and REST API; SNMPv2c/v3; HPE Aruba Networking Central; AirWave; CX Mobile App; "
                "Multi-Edit; Network Analytics Engine; USB-C console, OOBM and USB-A host ports"
            ),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE Aruba Networking CX 6300M JL658A specifications."
    products = PRODUCTS
    document_version = "Official HPE QuickSpecs version 42 (2025-11-03); accessed 2026-10-16"
