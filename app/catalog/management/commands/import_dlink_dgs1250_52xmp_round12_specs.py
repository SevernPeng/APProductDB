from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DS = "https://www.dlink.com/en/-/media/business_products/dgs/dgs-1250/dgs1250seriesdatasheetv109ww.pdf"


PRODUCTS = {
    "DGS-1250-52XMP": {
        "url": DS,
        "page": "pp. 4-7, DGS-1250-52XMP hardware column and standard-image software features",
        "title": "D-Link DGS-1250 Series Smart Managed Switches Datasheet v8.05 WW",
        "values": {
            "ethernet_interfaces": t(
                "48 x 10/100/1000BASE-T PoE; 4 x 10G SFP+; RJ-45 console port",
                "Interfaces: 48 x 10/100/1000BASE-T PoE and 4 x 10G SFP+ ports; full CLI via console port",
            ),
            "switching_capacity_gbps": n(176, "Switching capacity: 176 Gbps"),
            "packet_forwarding_rate_mpps": n(130.95, "Maximum 64-byte packet forwarding rate: 130.95 Mpps"),
            "packet_buffer_mb": n(2, "Packet buffer memory: 16 Mbits (2 MB)"),
            "poe_standard": t("IEEE 802.3af/at PoE/PoE+", "PoE standard: IEEE 802.3af/at"),
            "poe_ports": n(48, "PoE-capable ports: 48"),
            "poe_budget_w": n(370, "PoE power budget: 370 W"),
            "max_poe_per_port_w": n(30, "Maximum 30 W per port"),
            "max_power_consumption_w": n(467.3, "Maximum power consumption with PoE on: 467.3 W at 100 V; 443.6 W at 240 V"),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz universal power supply", "Power input: 100 to 240 V AC, 50/60 Hz internal universal power supply"),
            "dimensions_mm": t("440 x 250 x 44 mm", "Dimensions (L x W x H): 440 x 250 x 44 mm"),
            "fan_design": t("Smart fan", "Official product specification: Smart Fan"),
            "operating_temperature_c": t("-5 to 50 °C", "Operating temperature: -5 to 50 °C (23 to 122 °F)"),
            "jumbo_frame_bytes": n(12000, "Jumbo frame: Up to 12,000 bytes"),
            "vlan_count": n(4094, "Maximum 4094 static VLAN groups; configurable VID 1-4094"),
            "l2_features": t(
                "IGMP v1/v2/v3 and MLD v1/v2 snooping; 802.3ad link aggregation (8 groups, 8 ports/group); LLDP/LLDP-MED; port mirroring; 802.3x flow control; loopback detection; PD-Alive and optics DDM",
                "L2 features include IGMP/MLD snooping, 802.3ad link aggregation, LLDP/LLDP-MED, port mirroring, flow control, loopback detection, PD-Alive and DDM",
            ),
            "stp_features": t("IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP", "Spanning Tree Protocol: 802.1D STP, 802.1w RSTP and 802.1s MSTP"),
            "acl_security": t(
                "Up to 50 access lists and 768 shared IPv4/MAC/IPv6 rules; 802.1X, RADIUS/TACACS+, SSHv2, TLS 1.2, Safeguard Engine, DHCP snooping, ARP/IP inspection, IP-MAC-Port Binding, port security and DoS prevention",
                "ACL: maximum 50 lists and 768 rules shared by IPv4, MAC and IPv6; security includes 802.1X, RADIUS/TACACS+, SSHv2, TLS 1.2, DHCP snooping, inspections, Smart Binding and DoS prevention",
            ),
            "management_methods": t(
                "Web GUI; D-Link Network Assistant; full CLI via console; Telnet; TFTP; SNMP v1/v2c/v3; Syslog; SNTP; RMONv1; dual image and dual configuration",
                "Management: Web GUI, D-Link Network Assistant, full CLI, Telnet, TFTP, SNMP v1/v2c/v3, Syslog, SNTP, RMONv1, dual image and dual configuration",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified current D-Link DGS-1250-52XMP hardware and software specifications."
    products = PRODUCTS
    document_version = "v8.05 WW, updated 2024-10-16; accessed 2026-10-22"
    brand_name = "D-Link"
