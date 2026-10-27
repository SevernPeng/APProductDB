from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_NON_POE = "https://www.downloads.netgear.com/files/GDC/GS308Ev4/GS305E_GS308E_DS.pdf"
URL_POE = "https://www.downloads.netgear.com/files/GDC/GS324EP/GS305EP_GS305EPP_GS308EP_GS308EPP_GS316EP_GS316EPP_GS324EP_DS.pdf"


NON_POE_COMMON = {
    "jumbo_frame_bytes": n(9000, "Up to 9K packet size"),
    "l2_features": t(
        "IEEE 802.1Q and port-based VLANs; IGMP snooping v1/v2/v3; block unknown multicast; "
        "loop detection; broadcast storm control; port mirroring"
    ),
    "igmp_group_capacity": t("128 multicast groups", "Supported multicast groups: 128"),
    "dhcp_features": t("DHCP client"),
    "qos_support": t(
        "Rate limiting; IEEE 802.1p CoS; port-based QoS; WRR and strict-priority queuing"
    ),
    "acl_security": t("Automatic denial-of-service prevention; system password"),
    "management_methods": t("Web browser GUI and NETGEAR Plus Utility"),
    "lag_group_capacity": t("Not supported", "Link Aggregation/Port Trunking: No"),
    "cable_test": t("Cable Test Utility; loop detection and broadcast storm controls"),
    "fanless": b(True, "Acoustic noise level at 25 C: 0 dBA"),
    "fan_design": t("Fanless", "Acoustic noise level at 25 C: 0 dBA"),
    "power_supply": t("External power adapter"),
}


POE_COMMON = {
    "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
    "max_poe_per_port_w": n(30, "IEEE 802.3at: 30 W per port"),
    "mac_address_table": t("4K"),
    "packet_buffer_mb": n("0.188", "Buffer size: 192 KB (0.1875 MB; stored to three decimal places)"),
    "vlan_count": n(64),
    "l2_features": t(
        "IEEE 802.1Q and port-based VLANs; static LAG; IGMP snooping v1/v2/v3; "
        "block unknown multicast; port mirroring; broadcast storm control"
    ),
    "igmp_group_capacity": t("128 multicast groups", "Supported multicast groups: 128"),
    "dhcp_features": t("DHCP client"),
    "qos_support": t("Rate limiting; DSCP; IEEE 802.1p CoS; TOS; WRR queuing"),
    "acl_security": t("Automatic denial-of-service prevention; system password"),
    "management_methods": t("Web browser-based management GUI; configuration upload to server"),
    "cable_test": t("Cable Test Utility"),
    "fanless": b(True, "Acoustic noise level at 25 C: 0 dBA"),
    "fan_design": t("Fanless", "Acoustic noise level at 25 C: 0 dBA"),
    "power_supply": t("External power adapter"),
    "operating_temperature_c": t("0 to 40 °C"),
}


def non_poe(model, bandwidth, vlan_count, dimensions, temperature, ports):
    return {
        "url": URL_NON_POE,
        "page": "pp. 1-3, GS300 Series comparison and management tables",
        "title": "NETGEAR GS305E/GS308E Plus Gigabit Ethernet Switches Data Sheet",
        "values": {
            **NON_POE_COMMON,
            "ethernet_interfaces": t(f"{ports} x 10/100/1000BASE-T RJ45"),
            "switching_capacity_gbps": n(bandwidth),
            "vlan_count": n(vlan_count),
            "dimensions_mm": t(dimensions),
            "operating_temperature_c": t(temperature),
        },
    }


def poe(model, ports, poe_ports, budget, bandwidth, jumbo, lags, members, dimensions):
    sfp = 1 if ports == 16 else 0
    copper_text = f"{ports} x 10/100/1000BASE-T RJ45"
    if sfp:
        copper_text += "; 1 x 1G SFP"
    return {
        "url": URL_POE,
        "page": "pp. 2-3, technical specifications table",
        "title": "NETGEAR PoE+ Gigabit Ethernet Plus Switches Data Sheet",
        "values": {
            **POE_COMMON,
            "ethernet_interfaces": t(copper_text),
            "poe_ports": n(poe_ports),
            "poe_budget_w": n(budget),
            "poe_configuration": t(f"{poe_ports} PoE+ ports; {budget} W total budget"),
            "switching_capacity_gbps": n(bandwidth),
            "jumbo_frame_bytes": n(jumbo),
            "lag_group_capacity": t(f"{lags} static manual LAGs, up to {members} members each"),
            "dimensions_mm": t(dimensions),
        },
    }


PRODUCTS = {
    "GS305E": non_poe("GS305E", 10, 64, "94 x 100 x 27 mm (W x D x H)", "0 to 50 °C", 5),
    "GS308E": non_poe("GS308E", 16, 64, "158 x 101 x 29 mm (W x D x H)", "0 to 40 °C", 8),
    "GS305EP": poe("GS305EP", 5, 4, 63, 10, 9216, 1, 4, "158 x 101 x 27 mm (W x D x H)"),
    "GS308EPP": poe("GS308EPP", 8, 8, 123, 16, 9216, 2, 4, "158 x 101 x 27 mm (W x D x H)"),
    "GS316EP": poe("GS316EP", 16, 15, 180, 32, 10000, 8, 8, "286 x 102 x 27 mm (W x D x H)"),
    "GS316EPP": poe("GS316EPP", 16, 15, 231, 32, 10000, 8, 8, "286 x 102 x 27 mm (W x D x H)"),
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR GS300 Easy Smart switch specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR GS300 series datasheets; GS305E/GS308E revision D-GS305E/GS308E-24May24; accessed 2026-10-23"
    brand_name = "NETGEAR"
