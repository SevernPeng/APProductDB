from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://www.netgear.com/media/GC728X_GC728XP_GC752X_GC752XP_DS_tcm148-68959.pdf"


COMMON = {
    "packet_buffer_mb": n("1.5"),
    "jumbo_frame_bytes": n(9216),
    "vlan_count": n(256),
    "l2_features": t(
        "802.1Q, IP-, MAC-, protocol-, voice/video- and private VLANs; LACP/static LAG; "
        "LLDP/LLDP-MED; IGMP/MLD snooping; storm control; DHCP snooping"
    ),
    "stp_features": t("IEEE 802.1D STP; 802.1w RSTP; 802.1s MSTP"),
    "acl_security": t(
        "100 shared MAC/IPv4/IPv6 ACLs; IEEE 802.1X; RADIUS VLAN assignment; "
        "protected ports; DHCP snooping; configurable management VLAN"
    ),
    "l3_features": t("IPv4/IPv6 static routing and VLAN routing"),
    "ip_interface_capacity": t("15 routed VLAN interfaces"),
    "routing_entry_capacity": t("32 IPv4 static routes; 31 IPv6 static routes"),
    "management_methods": t(
        "NETGEAR Insight mobile app/Cloud Portal; local web GUI; SNMP v1/v2c/v3; "
        "RMON; HTTPS; TFTP/HTTP; USB configuration and firmware management"
    ),
    "operating_temperature_c": t("0 to 50 °C"),
}


def item(model, capacity, forwarding, max_power, dimensions, power_supply, fans, poe=None):
    values = {
        **COMMON,
        "switching_capacity_gbps": n(capacity, f"Non-blocking full-duplex bandwidth: {capacity} Gbps"),
        "packet_forwarding_rate_mpps": n(forwarding),
        "max_power_consumption_w": n(max_power),
        "dimensions_mm": t(dimensions),
        "power_supply": t(power_supply),
        "fan_design": t(f"{fans} internal temperature/load-controlled fixed fan{'s' if fans != 1 else ''}"),
    }
    if poe:
        ports, budget = poe
        values.update({
            "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
            "poe_ports": n(ports),
            "poe_budget_w": n(budget),
            "max_poe_per_port_w": n(30),
        })
    return {
        "url": URL,
        "page": f"pp. 4, 10-17, {model} hardware/performance/software tables",
        "title": "NETGEAR GC728X/GC728XP/GC752X/GC752XP Data Sheet",
        "values": values,
    }


PRODUCTS = {
    "GC728X": item("GC728X", 92, "68.5", "18.5", "440 x 224 x 44 mm (W x D x H)",
                   "Internal fixed 100-240 VAC, 50-60 Hz, 1 A maximum", 1),
    "GC728XP": item("GC728XP", 92, "68.5", "437.1", "440 x 224 x 44 mm (W x D x H)",
                    "Internal fixed 100-240 VAC, 50-60 Hz, 10 A maximum", 2, (24, 390)),
    "GC752X": item("GC752X", 140, "104.2", "43.9", "440 x 224 x 44 mm (W x D x H)",
                   "Internal fixed 100-240 VAC, 50-60 Hz, 1.5 A maximum", 1),
    "GC752XP": item("GC752XP", 140, "104.2", "623.6", "440 x 320 x 44 mm (W x D x H)",
                    "Internal fixed 100-240 VAC, 50-60 Hz, 10 A maximum", 3, (48, 505)),
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR GC700-series switch specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR GC700 series datasheet, current 2026 revision; accessed 2026-10-20"
    brand_name = "NETGEAR"
