from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


FS728TP_URL = (
    "https://www.downloads.netgear.com/files/GDC/datasheet/en/"
    "FS526T-FS726T-FS728TLP-FS728TP-FS750T2.pdf"
)
GS305EP_URL = (
    "https://www.downloads.netgear.com/files/GDC/GS324EP/"
    "GS305EP_GS305EPP_GS308EP_GS308EPP_GS316EP_GS316EPP_GS324EP_DS.pdf"
)
GS308E_URL = (
    "https://www.downloads.netgear.com/files/GDC/GS308Ev4/"
    "GS305E_GS308E_DS.pdf"
)
GS516TP_URL = (
    "https://www.downloads.netgear.com/files/GDC/datasheet/en/"
    "GS516TP-GS728TP-GS728TPP-GS752TP.pdf"
)
GS716T_URL = (
    "https://www.downloads.netgear.com/files/GDC/GS716TV3/"
    "GS716Tv3_DS.pdf"
)
MS108EUP_URL = (
    "https://www.downloads.netgear.com/files/GDC/MS108EUP/"
    "MS108EUP_DS.pdf"
)


def forwarding(value, bandwidth):
    return n(
        value,
        (
            "Derived 64-byte line-rate forwarding from the official non-blocking "
            f"switching bandwidth: {bandwidth} Gbps x 0.744 Mpps/Gbps = "
            f"{bandwidth * 0.744:.3f} Mpps; stored rounded to {value} Mpps"
        ),
    )


PRODUCTS = {
    "FS728TP": {
        "url": FS728TP_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR ProSAFE Smart Switches FS526T/FS726T/FS728TLP/FS728TP/FS750T2 Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(9.52, 12.8),
        },
    },
    "GS305EP": {
        "url": GS305EP_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR Gigabit Ethernet Plus PoE Switches Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(7.44, 10),
        },
    },
    "GS308E": {
        "url": GS308E_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR GS305E/GS308E Gigabit Ethernet Plus Switches Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(11.90, 16),
        },
    },
    "GS516TP": {
        "url": GS516TP_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR ProSAFE Gigabit Smart Managed PoE Switches Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(23.81, 32),
        },
    },
    "GS716Tv3": {
        "url": GS716T_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR GS716Tv3/GS724Tv4/GS748Tv5 Smart Switches Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(26.78, 36),
        },
    },
    "GS748T": {
        "url": GS716T_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR GS716Tv3/GS724Tv4/GS748Tv5 Smart Switches Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(74.40, 100),
        },
    },
    "MS108EUP": {
        "url": MS108EUP_URL,
        "page": "Technical specifications table",
        "title": "NETGEAR MS108EUP Multi-Gigabit Ethernet Plus PoE Switch Datasheet",
        "values": {
            "packet_forwarding_rate_mpps": forwarding(29.76, 40),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified, deterministically derived NETGEAR 64-byte forwarding rates."
    products = PRODUCTS
    document_version = "Official NETGEAR datasheets; manually verified and accessed 2026-10-27"
    brand_name = "NETGEAR"
