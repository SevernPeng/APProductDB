from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DS = "https://meweb.dlink.com/en/-/media/business_products/des/des-1210-series/datasheet/des_1210_series_datasheet_en_eu.pdf"


PRODUCTS = {
    "DES-1210-28P": {
        "url": DS,
        "page": "pp. 3-5, DES-1210-28P C1 hardware and common software specifications",
        "title": "D-Link DES-1210 Series Fast Ethernet Smart Managed Switches Datasheet",
        "values": {
            "ethernet_interfaces": t(
                "24 x 10/100BASE-TX PoE; 2 x 10/100/1000BASE-T; 2 x combo 10/100/1000BASE-T / 100/1000SFP",
                "DES-1210-28P interface: 24 10/100BASE-TX PoE, 2 10/100/1000BASE-T and 2 combo 10/100/1000BASE-T/100/1000SFP",
            ),
            "switching_capacity_gbps": n(12.8, "Switching capacity: 12.8 Gbps"),
            "packet_forwarding_rate_mpps": n(9.5, "64-byte maximum forwarding rate: 9.5 Mpps"),
            "packet_buffer_mb": n(0.512, "Packet buffer memory: 4.1 Mbits (normalized to 0.512 MB at database precision)"),
            "poe_standard": t("IEEE 802.3af/at PoE/PoE+", "PoE standard: IEEE 802.3af and IEEE 802.3at (C1)"),
            "poe_ports": n(24, "24 PoE-capable 10/100BASE-TX ports"),
            "poe_budget_w": n(193, "PoE power budget: 193 watts"),
            "max_poe_per_port_w": n(30, "Ports 1-4 support up to 30 W; ports 5-24 support up to 15.4 W"),
            "max_power_consumption_w": n(240, "Maximum power consumption: 240 W with PoE on; 17.9 W with PoE off"),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz universal power supply", "Power input: 100 to 240 VAC, 50 to 60 Hz internal universal power supply"),
            "dimensions_mm": t("440 x 210 x 44 mm", "Dimensions (W x D x H): 440 x 210 x 44 mm"),
            "fan_design": t("3 smart fans", "Cooling fans: 3 smart fans"),
            "operating_temperature_c": t("-5 to 50 °C", "Operation temperature: -5 to 50 °C (23 to 122 °F)"),
            "vlan_count": n(256, "Maximum 256 static VLAN groups; maximum 4094 VIDs"),
            "l2_features": t(
                "802.3x flow control; HOL blocking prevention; port mirroring; 802.3ad link aggregation (8 groups, 8 ports/group); IGMP v1/v2/v3 and MLD v1/v2 snooping; loopback detection and cable diagnostics",
                "L2 features include flow control, port mirroring, 802.3ad link aggregation, IGMP/MLD snooping, loopback detection and cable diagnostics",
            ),
            "stp_features": t(
                "IEEE 802.1D STP (2004), IEEE 802.1w RSTP and Root Restriction",
                "Spanning Tree: 802.1D STP 2004, 802.1w RSTP and Root Restriction",
            ),
            "acl_security": t(
                "Up to 50 ingress ACL profiles and 1,280 ingress ACL rules with L2-L4 and IPv6 classifiers; 802.1X, RADIUS, Safeguard Engine, DHCP Server Screening, ARP spoofing prevention, port security, DoS prevention and IP-MAC-Port Binding",
                "ACL: maximum 50 ingress profiles and 1280 ingress rules; security includes 802.1X/RADIUS, Safeguard Engine, DHCP Server Screening, ARP spoofing prevention, port security, DoS prevention and Smart Binding",
            ),
            "management_methods": t(
                "Web GUI; D-Link Network Assistant/SmartConsole; compact CLI and Telnet; SNMP v1/v2c/v3; Syslog; SSHv2; TFTP; LLDP/LLDP-MED; SNTP; RMON; D-View",
                "Management: Web GUI, Network Assistant/SmartConsole, compact CLI through Telnet, SNMP v1/v2c/v3, Syslog, SSHv2, TFTP, LLDP/LLDP-MED, SNTP, RMON and D-View",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified latest-revision D-Link DES-1210-28P C1 hardware and software specifications."
    products = PRODUCTS
    document_version = "DES-1210-28P C1, datasheet updated October 2015; accessed 2026-10-22"
    brand_name = "D-Link"
