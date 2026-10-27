from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL = "https://www2.dlink.com/en/-/media/business_products/dms/dms-1100-10ts/datasheet/dms1100seriesa1datasheetv120ww.pdf"


COMMON = {
    "switching_capacity_gbps": n(80, "Switching capacity: 80 Gbps"),
    "packet_forwarding_rate_mpps": n(59.52, "Maximum packet forwarding rate: 59.52 Mpps"),
    "mac_address_table": t("Up to 16,000 entries per device"),
    "packet_buffer_mb": n(1.5, "Packet buffer: 12 Mbits (1.5 MB)"),
    "jumbo_frame_bytes": n(9216, "Jumbo frames up to 9216 bytes"),
    "vlan_count": n(4094, "Supports 4094 static VLAN groups; maximum 4094 VIDs"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
    "l2_features": t("802.1Q and port-based VLAN; asymmetric, voice and surveillance VLAN; LACP; IGMP/MLD snooping; port mirroring; G.8032 ERPS"),
    "management_methods": t("Web GUI; SmartConsole Utility; SNMP v1/v2c/v3; RMON; LLDP/LLDP-MED"),
    "operating_temperature_c": t("-5 to 50 °C"),
    "power_supply": t("Internal 100 to 240 V AC power supply"),
}


PRODUCTS = {
    model: {
        "url": URL,
        "title": "D-Link DMS-1100 Series Datasheet, version 1.20WW",
        "page": f"Technical specifications and software features - {model}",
        "values": COMMON,
    }
    for model in ("DMS-1100-10TS", "DMS-1100-10TP")
}


class Command(VerifiedImportCommand):
    help = "Import DMS-1100 series performance, jumbo, VLAN, L2, environmental, and power specifications."
    products = PRODUCTS
    document_version = "1.20WW; accessed 2026-10-21"
    brand_name = "D-Link"
