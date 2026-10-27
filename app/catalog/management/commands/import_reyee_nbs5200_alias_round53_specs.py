from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


SOURCE_URL = "https://reyee.ruijie.com/en-global/products/reyee-switch/l3-managed-switch/rg-nbs5200-24sfp-8gt4xs/"


PRODUCTS = {
    "RGNBS5200-24SFP": {
        "url": SOURCE_URL,
        "page": (
            "Exact RG-NBS5200-24SFP/8GT4XS specification tables; "
            "the imported database alias omits separators and the /8GT4XS suffix"
        ),
        "title": "Reyee RG-NBS5200-24SFP/8GT4XS official product page and datasheet",
        "values": {
            "ethernet_interfaces": t("24 x 1GbE SFP including 8 combo GbE RJ45 ports; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(96),
            "jumbo_frame_bytes": n(9216, "Jumbo frame length (MTU): 9216 bytes"),
            "packet_buffer_mb": n(1.5, "Packet buffer: 12 Mbit (1.5 MB)"),
            "mac_address_table": t("16K", "MAC address table: 16,000 entries"),
            "vlan_count": n(4094, "Maximum VLAN support: 4094"),
            "management_methods": t("Ruijie Cloud web portal and mobile app; local eWeb management"),
            "l2_features": t("Link aggregation; IGMP snooping; VLAN; port isolation; broadcast storm control"),
            "stp_features": t("STP and RSTP"),
            "acl_security": t("ACL; port isolation; broadcast storm control; multiple security policies"),
            "l3_features": t("Static routing; RIP; OSPF; Virtual Cluster Switching (VCS)"),
            "ospf_support": b(True),
            "rip_support": b(True),
            "stacking": t("Virtual Cluster Switching (VCS) hot standby"),
            "stacking_units": n(2, "Only two switches can form a VCS hot-standby group"),
            "routing_entry_capacity": t("IPv4 routing table: 6000 entries; IPv4 static routes: 500"),
            "dimensions_mm": t("440 x 267.5 x 43.6 mm (W x D x H)"),
            "max_power_consumption_w": n(41.8, "Maximum power consumption: 41.8 W"),
            "power_supply": t("Fixed AC power supply, 100-240 V, 50/60 Hz, maximum input current 2 A"),
            "fan_design": t("2 x fixed fans; left-to-right airflow"),
            "flash_memory": t("256 MB"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact Reyee RG-NBS5200-24SFP/8GT4XS specs for its legacy database alias."
    products = PRODUCTS
    document_version = "Exact-model official datasheet 2025-10-28 and current product page; accessed 2026-10-22"
    brand_name = "Reyee"
