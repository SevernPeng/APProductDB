from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


FS728TP_DS = "https://www.downloads.netgear.com/files/GDC/datasheet/en/FS526T-FS726T-FS728TLP-FS728TP-FS750T2.pdf"
GS700T_DS = "https://www.downloads.netgear.com/files/GDC/GS716TV3/GS716Tv3_DS.pdf"
GS516TP_DS = "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS516TP-GS728TP-GS728TPP-GS752TP.pdf"
MS108EUP_DS = "https://www.downloads.netgear.com/files/GDC/MS108EUP/MS108EUP_DS.pdf"


PRODUCTS = {
    "FS728TP": {
        "url": FS728TP_DS,
        "page": "pp. 6-8, L2 Services and IEEE Network Protocols, FS728TP column",
        "title": "NETGEAR FS526T/FS728TLP/FS728TP/FS750T2 Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t(
                "IEEE 802.1Q tagged, IP-based, MAC-based, and voice VLANs",
                "128 VLANs; IEEE 802.1Q, IP-based, MAC-based, and voice VLAN support",
            ),
        },
    },
    "GS716Tv3": {
        "url": GS700T_DS,
        "page": "pp. 8-10, L2 Services and IEEE Network Protocols, GS716T column",
        "title": "NETGEAR GS716T/GS724T/GS748T Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t(
                "IEEE 802.1Q tagged, protocol-based, MAC-based, voice, guest, and dynamic RADIUS-assigned VLANs"
            ),
        },
    },
    "GS748T": {
        "url": GS700T_DS,
        "page": "pp. 8-10, L2 Services and IEEE Network Protocols, GS748T column",
        "title": "NETGEAR GS716T/GS724T/GS748T Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t(
                "IEEE 802.1Q tagged, protocol-based, MAC-based, voice, guest, and dynamic RADIUS-assigned VLANs"
            ),
        },
    },
    "GS516TP": {
        "url": GS516TP_DS,
        "page": "pp. 5-6, IEEE Network Protocols and L2 Services",
        "title": "NETGEAR GS516TP/GS728TP/GS728TPP/GS752TP Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t(
                "IEEE 802.1Q tagged, guest, dynamic RADIUS-assigned, voice, and video VLANs"
            ),
        },
    },
    "MS108EUP": {
        "url": MS108EUP_DS,
        "page": "pp. 3-4, L2 Services and IEEE Network Protocols",
        "title": "NETGEAR MS108EUP Multi-Gigabit Ethernet Plus Switch Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t("IEEE 802.1Q tagged and port-based VLANs"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified NETGEAR legacy/Plus switch flow-control and VLAN specifications."
    products = PRODUCTS
    document_version = "Current official NETGEAR data sheets; accessed 2026-10-23"
    brand_name = "NETGEAR"
