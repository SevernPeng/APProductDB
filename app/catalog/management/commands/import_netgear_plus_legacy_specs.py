from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


URL_100 = "https://www.downloads.netgear.com/files/GDC/Switches/GS105E_GS108E_DS.pdf"
URL_PLUS = "https://www.downloads.netgear.com/files/GDC/Gigabit_Ethernet_Plus_Switches_DS.pdf"


COMMON = {
    "management_type": t("NETGEAR Plus web managed; PC Utility"),
    "vlan_support": t("IEEE 802.1Q tagged and port-based VLANs"),
    "port_mirroring": t("Many-to-one port mirroring"),
    "igmp_snooping": t("IGMP snooping v1, v2 and v3; block unknown multicast"),
    "loop_prevention": b(True, "Loop Detection: Yes"),
    "cable_test": t("Cable Test utility"),
    "flow_control": t("IEEE 802.3x full-duplex flow control"),
    "qos_support": t("Rate limiting; IEEE 802.1p CoS; TOS; WRR"),
    "fanless": b(True, "Fan count: 0"),
    "installation": t("Desktop or wall mount"),
}


def item(model, url, page, title, ports, bandwidth, mac, buffer_mb, jumbo, vlans,
         link_aggregation, dimensions, max_power, temperature):
    return {
        "url": url,
        "page": page,
        "title": title,
        "values": {
            **COMMON,
            "ethernet_interfaces": t(f"{ports} x 10/100/1000BASE-T RJ45"),
            "switching_capacity_gbps": n(bandwidth),
            "mac_address_table": t(f"{mac:,} entries"),
            "packet_buffer_mb": n(buffer_mb),
            "jumbo_frame_bytes": n(jumbo),
            "vlan_count": n(vlans),
            "link_aggregation": t("8 static manual LAGs, 2 to 4 members" if link_aggregation else "Not supported", "Static manual LAGs only" if link_aggregation else "Link Aggregation/Port Trunking: No"),
            "dimensions_mm": t(dimensions),
            "max_power_consumption_w": n(max_power),
            "operating_temperature_c": t(temperature),
        },
    }


PRODUCTS = {
    "GS105E": item(
        "GS105E", URL_100, "pp. 3-5, GS100 Series comparison tables",
        "NETGEAR GS105E/GS108E Plus Gigabit Ethernet Switch Data Sheet (30 May 2024)",
        5, 10, 2000, "0.125", 9000, 64, False,
        "94 x 100 x 27 mm (W x D x H)", "2.6", "0 to 50 °C",
    ),
    "GS108E": item(
        "GS108E", URL_100, "pp. 3-5, GS100 Series comparison tables",
        "NETGEAR GS105E/GS108E Plus Gigabit Ethernet Switch Data Sheet (30 May 2024)",
        8, 16, 4000, "0.188", 9000, 64, False,
        "158 x 101 x 29 mm (W x D x H)", "4.5", "0 to 40 °C",
    ),
    "GS116E": item(
        "GS116E", URL_PLUS, "pp. 2-7, hardware/software and technical specifications tables",
        "NETGEAR Gigabit Ethernet Plus Switches Data Sheet",
        16, 32, 16000, "0.750", 9000, 100, True,
        "286 x 101 x 26 mm (W x D x H)", 10, "0 to 40 °C",
    ),
}


class Command(VerifiedImportCommand):
    help = "Import manually verified NETGEAR GS105E, GS108E and GS116E specifications."
    products = PRODUCTS
    document_version = "Official NETGEAR Plus switch datasheets; accessed 2026-10-20"
    brand_name = "NETGEAR"
