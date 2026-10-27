from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


GS300_DS = "https://www.netgear.com/images/datasheet/switches/WebManagedSwitches/GS305E_GS308E.pdf"
GS300_POE_UM = "https://www.downloads.netgear.com/files/GDC/GS305EP/GS305EP-EPP_GS308EP-EPP_UM_EN.pdf"
GS316_POE_UM = "https://www.downloads.netgear.com/files/GDC/GS316EP/GS316EP_GS316EPP_UM_EN.pdf"


PRODUCTS = {
    "GS305E": {
        "url": GS300_DS,
        "page": "p. 1, Highlights",
        "title": "NETGEAR GS305E/GS308E Smart Managed Plus Switches Data Sheet",
        "values": {
            "stp_features": t(
                "Loop detection (not STP/RSTP)",
                "Official data sheet lists loop detection and broadcast storm controls",
            ),
        },
    },
    "GS308E": {
        "url": GS300_DS,
        "page": "p. 1, Highlights",
        "title": "NETGEAR GS305E/GS308E Smart Managed Plus Switches Data Sheet",
        "values": {
            "stp_features": t(
                "Loop detection (not STP/RSTP)",
                "Official data sheet lists loop detection and broadcast storm controls",
            ),
        },
    },
    "GS305EP": {
        "url": GS300_POE_UM,
        "page": "Chapter 7, Enable or disable loop detection",
        "title": "NETGEAR GS305EP/EPP and GS308EP/EPP User Manual",
        "values": {
            "stp_features": t(
                "Loop detection (not STP/RSTP)",
                "The user manual provides an explicit loop-detection control",
            ),
        },
    },
    "GS308EPP": {
        "url": GS300_POE_UM,
        "page": "Chapter 7, Enable or disable loop detection",
        "title": "NETGEAR GS305EP/EPP and GS308EP/EPP User Manual",
        "values": {
            "stp_features": t(
                "Loop detection (not STP/RSTP)",
                "The user manual provides an explicit loop-detection control",
            ),
        },
    },
    "GS316EP": {
        "url": GS316_POE_UM,
        "page": "p. 119, Enable or disable loop prevention",
        "title": "NETGEAR GS316EP and GS316EPP User Manual",
        "values": {
            "stp_features": t(
                "Loop prevention (not STP/RSTP)",
                "Loop prevention is enabled by default and signals a detected loop through port LEDs",
            ),
        },
    },
    "GS316EPP": {
        "url": GS316_POE_UM,
        "page": "p. 119, Enable or disable loop prevention",
        "title": "NETGEAR GS316EP and GS316EPP User Manual",
        "values": {
            "stp_features": t(
                "Loop prevention (not STP/RSTP)",
                "Loop prevention is enabled by default and signals a detected loop through port LEDs",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified NETGEAR Easy Smart loop-detection/prevention specifications."
    products = PRODUCTS
    document_version = "Current official data sheets and user manuals; accessed 2026-10-22"
    brand_name = "NETGEAR"
