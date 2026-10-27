from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/04b68e939d0a4b1da33bb2b4ab3435c5/M3T1A590N1221516154371072217/Huawei%20CloudEngine%20S5735-S-V2%20Series%202_5GE%20Switches%20Datasheet.pdf"

COMMON = {
    "vlan_count": n(4094),
    "l2_features": t(
        "Voice/MUX VLAN; basic/selective QinQ; VLAN stacking and mapping; Smart Link; SEP; "
        "ERPS G.8032; LLDP; IGMP/MLD snooping; port mirroring"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU, root, and loop protection"
    ),
    "acl_security": t(
        "IPv4/IPv6 hardware ACLs and Layer 2-4 filtering; 802.1X/MAC authentication; "
        "AAA/RADIUS/HWTACACS/NAC; DHCP snooping; port isolation/security; CPU and DoS/ARP/ICMP defense"
    ),
    "management_methods": t(
        "CLI; SSHv2; SNMPv1/v2c/v3; Web NMS; RMON; NETCONF/YANG cloud management; "
        "WebMaster; telemetry"
    ),
    "stacking": t("Huawei iStack using two dedicated 12GE stack ports"),
    "stacking_units": n(9),
    "routing_entry_capacity": t("Up to 8192 IPv4 FIB entries and 4000 IPv6 FIB entries"),
    "ospf_support": b(True),
    "rip_support": b(True),
    "pbr_support": b(True),
    "vrrp_support": b(True),
    "multicast_routing": b(True, "PIM-DM, PIM-SM, PIM-SSM, and PIMv6"),
    "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
    "operating_temperature_c": t(
        "-5 to 50 °C at 0-1800 m; maximum temperature derates 1 °C per 220 m above 1800 m"
    ),
    "management_interfaces": t("Console (RJ45); USB 2.0"),
    "switch_usb_interfaces": t("1 x USB 2.0"),
    "cpu": t("1.1 GHz, 2 cores"),
    "mac_address_table": t("32K entries maximum"),
    "redundant_power": b(True),
    "max_poe_per_port_w": n(30, "IEEE 802.3at PoE+ per port"),
}

PRODUCTS = {
    "S5735-S24PN4XE-V2": {
        "url": SOURCE_URL,
        "page": "Models, power configurations, functions, and hardware specifications tables",
        "title": "Huawei CloudEngine S5735-S-V2 Series 2.5GE Switches Datasheet",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(248, "Device value before the slash in 248/520 Gbps"),
            "packet_forwarding_rate_mpps": n(144),
            "poe_ports": n(24),
            "poe_budget_w": n(840, "Maximum available PoE power with supported power configuration"),
            "max_power_consumption_w": n(1070.85, "With PD load of 840 W"),
            "power_supply": t("Pluggable power modules; 1+1 redundancy"),
            "fan_design": t("1 fan module; air-cooled with intelligent speed adjustment"),
        },
    },
    "S5735-S48PN4XE-V2": {
        "url": SOURCE_URL,
        "page": "Models, power configurations, functions, and hardware specifications tables",
        "title": "Huawei CloudEngine S5735-S-V2 Series 2.5GE Switches Datasheet",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(368, "Device value before the slash in 368/520 Gbps"),
            "packet_forwarding_rate_mpps": n(276),
            "poe_ports": n(48),
            "poe_budget_w": n(1680, "Maximum PD power in the maximum-consumption configuration"),
            "max_power_consumption_w": n(2019.68, "With PD load of 1680 W"),
            "power_supply": t("Pluggable power modules; 1+1+1 redundancy"),
            "fan_design": t("2 fan modules; air-cooled with intelligent speed adjustment"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import and repair Huawei CloudEngine S5735-S-V2 2.5GE switch specifications."
    products = PRODUCTS
    document_version = "Official global datasheet published 2026; accessed 2026-10-20"
    brand_name = "Huawei"
