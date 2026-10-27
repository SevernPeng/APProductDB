from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/"
    "HPE%20Aruba%20Networking%20CX%208360%20Switch%20Series-a00094643enw.pdf"
    "?deepLink=&form=false&hf=regular&id=a00094643enw.pdf&isFutureVersion=true"
    "&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section="
    "&softrollSection=&ver=15"
)


PRODUCTS = {
    "CX8360-32Y4C": {
        "url": URL,
        "page": "QuickSpecs v15 pages 2-8 and 27-28; JL700A/JL701A 8360-32Y4C columns",
        "title": "HPE Aruba Networking CX 8360 Switch Series QuickSpecs, version 15",
        "values": {
            "dimensions_mm": t("442.5 x 406.4 x 44.0 mm (W x D x H)"),
            "switching_capacity_gbps": n(2400, "High-performance 2.4 Tbps switching capacity"),
            "jumbo_frame_bytes": n(9000, "Maximum frame size: 9K bytes"),
            "vlan_count": n(4094, "Supports up to 4,094 port-based or IEEE 802.1Q VLANs"),
            "routing_entry_capacity": t(
                "606,977 IPv4 unicast routes; 630,784 IPv6 unicast routes"
            ),
            "l2_features": t(
                "IEEE 802.1Q VLAN and VLAN translation; STP/RSTP/MSTP/RPVST+; "
                "IGMP/MLD snooping; LACP; static and BGP-EVPN VXLAN; port mirroring"
            ),
            "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP, IEEE 802.1s MSTP and RPVST+"),
            "ospf_support": b(True, "OSPFv2 and OSPFv3 are supported"),
            "rip_support": b(True, "RIPv2 and RIPng are supported"),
            "pbr_support": b(True, "Policy-Based Routing (PBR) is supported"),
            "stacking": t(
                "Virtual Switching Extension (VSX) active-active two-switch architecture"
            ),
            "stacking_units": n(2, "VSX deploys two synchronized switches with independent control"),
            "management_methods": t(
                "ArubaOS-CX CLI and REST API; Aruba CX Mobile App; Aruba NetEdit; "
                "Network Analytics Engine; RJ-45 serial and USB-C console; "
                "RJ-45 Ethernet management and USB Type-A"
            ),
            "operating_temperature_c": t(
                "0 to 45 °C (port-to-power JL700A); 0 to 40 °C (power-to-port JL701A), up to 5,000 ft"
            ),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE Aruba Networking CX 8360-32Y4C gap specifications."
    products = PRODUCTS
    document_version = "Official HPE QuickSpecs version 15 (2023-02-06); accessed 2026-10-22"
