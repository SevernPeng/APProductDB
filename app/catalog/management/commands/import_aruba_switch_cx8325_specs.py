from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = "https://www.hpe.com/us/en/collaterals/collateral.a00056519enw.html"
TITLE = "HPE Aruba Networking CX 8325 Switch Series QuickSpecs, version 48"


COMMON = {
    "fanless": b(False, "The platform uses up to six field-replaceable, hot-swappable fans"),
    "redundant_power": b(True, "Supports up to two redundant, load-sharing, hot-swappable power supplies"),
    "operating_temperature_c": t("0 to 40 °C up to 10,000 ft"),
    "jumbo_frame_bytes": n(9000, "Official QuickSpecs state a 9K-byte maximum frame size"),
    "igmp_group_capacity": t("4,094 IGMP groups"),
    "mld_snooping": b(True, "MLDv1/v2 and IGMP/MLD snooping are supported; table capacity is 4,094 MLD groups"),
    "vlan_count": n(4040, "Supports up to 4,040 port-based or IEEE 802.1Q VLANs"),
    "l2_features": t(
        "802.1Q VLAN and VLAN translation; STP/RSTP/MSTP/RPVST+; IGMP/MLD snooping; "
        "LACP; static and BGP-EVPN VXLAN; port mirroring"
    ),
    "stp_features": t("IEEE 802.1D STP, 802.1w RSTP, 802.1s MSTP and RPVST+"),
    "lag_group_capacity": t("Up to 54 LAGs with eight links per group"),
    "dhcp_features": t("IPv4/IPv6 DHCP server, client, relay, smart relay and relay/server coexistence"),
    "routing_entry_capacity": t("131,072 IPv4 unicast routes; 32,732 IPv6 unicast routes"),
    "ospf_support": b(True, "OSPFv2 and OSPFv3 are supported"),
    "rip_support": b(True, "RIPv2/RIPng is supported"),
    "pbr_support": b(True, "Policy-Based Routing is supported"),
    "sdn_support": b(True, "AOS-CX provides built-in REST APIs, programmability and automation"),
    "stacking": t("Virtual Switching Extension (VSX) active-active two-switch architecture"),
    "stacking_units": n(2, "VSX is deployed as two synchronized switches with independent control"),
    "management_methods": t(
        "AOS-CX CLI and REST API; SNMPv2c/v3; CX Mobile App; NetEdit; Network Analytics Engine; "
        "RJ-45 serial, USB micro-USB console and RJ-45 Ethernet management port"
    ),
}


PRODUCTS = {
    "CX 8325-48Y8C JL635A": {
        "url": URL,
        "page": "Standard Features and JL624A/JL625A technical specifications for JL635A base chassis",
        "title": TITLE,
        "values": {
            **COMMON,
            "dimensions_mm": t("438.4 x 536 x 43.5 mm (W x D x H)"),
            "max_power_consumption_w": n(586, "Maximum AC-bundle power consumption"),
        },
    },
    "CX 8325-32C JL636A": {
        "url": URL,
        "page": "Standard Features and JL626A/JL627A technical specifications for JL636A base chassis",
        "title": TITLE,
        "values": {
            **COMMON,
            "dimensions_mm": t("442.5 x 473 x 43.95 mm (W x D x H)"),
            "max_power_consumption_w": n(618, "Maximum AC-bundle power consumption"),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE Aruba Networking CX 8325 base-chassis specifications."
    products = PRODUCTS
    document_version = "Official HPE QuickSpecs version 48 (2026-06-15); accessed 2026-10-16"
