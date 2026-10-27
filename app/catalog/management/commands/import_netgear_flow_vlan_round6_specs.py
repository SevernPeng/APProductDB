from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


GS608_DS = "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS605-GS608.pdf"
MS105_DS = "https://www.downloads.netgear.com/files/GDC/MS105/MS105_DS.pdf"
GS300_DS = "https://www.netgear.com/images/datasheet/switches/WebManagedSwitches/GS305E_GS308E.pdf"
GS300_POE_UM = "https://www.downloads.netgear.com/files/GDC/GS305EP/GS305EP-EPP_GS308EP-EPP_UM_EN.pdf"
GS316_POE_UM = "https://www.downloads.netgear.com/files/GDC/GS316EP/GS316EP_GS316EPP_UM_EN.pdf"


def easy_smart_values():
    return {
        "flow_control": t(
            "IEEE 802.3x flow control, configurable per port",
            "Official manual provides a per-port flow-control control",
        ),
        "vlan_support": t(
            "Port-based VLANs; basic and advanced IEEE 802.1Q VLANs",
            "Official manual documents port-based, basic 802.1Q, and advanced 802.1Q VLAN modes",
        ),
    }


PRODUCTS = {
    "GS608": {
        "url": GS608_DS,
        "page": "p. 2, Standards Compliance",
        "title": "NETGEAR GS605v3/GS608 Gigabit Ethernet Switches Data Sheet",
        "values": {
            "flow_control": t(
                "IEEE 802.3x full-duplex flow control",
                "IEEE 802.3x Full-duplex flow control",
            ),
        },
    },
    "MS105": {
        "url": MS105_DS,
        "page": "p. 3, IEEE Network Protocols",
        "title": "NETGEAR MS105 Multi-Gigabit Ethernet Unmanaged Switch Data Sheet",
        "values": {
            "flow_control": t(
                "IEEE 802.3x full-duplex flow control",
                "IEEE 802.3x Full-duplex Flow Control",
            ),
        },
    },
    "GS305E": {
        "url": GS300_DS,
        "page": "pp. 2-3, L2 Services - VLANs and IEEE Network Protocols",
        "title": "NETGEAR GS305E/GS308E Smart Managed Plus Switches Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t("IEEE 802.1Q tagged and port-based VLANs"),
        },
    },
    "GS308E": {
        "url": GS300_DS,
        "page": "pp. 2-3, L2 Services - VLANs and IEEE Network Protocols",
        "title": "NETGEAR GS305E/GS308E Smart Managed Plus Switches Data Sheet",
        "values": {
            "flow_control": t("IEEE 802.3x full-duplex flow control"),
            "vlan_support": t("IEEE 802.1Q tagged and port-based VLANs"),
        },
    },
    "GS305EP": {
        "url": GS300_POE_UM,
        "page": "pp. 21 and 24-47, flow control and supported VLAN modes",
        "title": "NETGEAR GS305EP/EPP and GS308EP/EPP User Manual, July 2026",
        "values": easy_smart_values(),
    },
    "GS308EPP": {
        "url": GS300_POE_UM,
        "page": "pp. 21 and 24-47, flow control and supported VLAN modes",
        "title": "NETGEAR GS305EP/EPP and GS308EP/EPP User Manual, July 2026",
        "values": easy_smart_values(),
    },
    "GS316EP": {
        "url": GS316_POE_UM,
        "page": "pp. 21 and 24-52, flow control and supported VLAN modes",
        "title": "NETGEAR GS316EP and GS316EPP User Manual, July 2026",
        "values": easy_smart_values(),
    },
    "GS316EPP": {
        "url": GS316_POE_UM,
        "page": "pp. 21 and 24-52, flow control and supported VLAN modes",
        "title": "NETGEAR GS316EP and GS316EPP User Manual, July 2026",
        "values": easy_smart_values(),
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified NETGEAR switch flow-control and VLAN-mode specifications."
    products = PRODUCTS
    document_version = "Current official data sheets and July 2026 user manuals; accessed 2026-10-23"
    brand_name = "NETGEAR"
