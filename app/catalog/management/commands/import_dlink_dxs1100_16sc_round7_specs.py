from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DXS1100_DS = "https://www.dlink.com/en/-/media/business_products/dxs/dxs-1100-10ts/dxs_1100_series_datasheet_en_eu.pdf"


PRODUCTS = {
    "DXS-1100-16SC": {
        "url": DXS1100_DS,
        "page": "pp. 3-5, DXS-1100-16SC column and software features",
        "title": "D-Link DXS-1100 Series 10 Gigabit Ethernet Smart Managed Switches Data Sheet",
        "values": {
            "switching_capacity_gbps": n(320, "DXS-1100-16SC switching capacity: 320 Gbps"),
            "packet_forwarding_rate_mpps": n(238.096, "DXS-1100-16SC maximum forwarding rate: 238.096 Mpps"),
            "packet_buffer_mb": n(2, "Packet buffer: 2 MB"),
            "jumbo_frame_bytes": n(9216, "Jumbo Frame: Up to 9,216 Bytes"),
            "vlan_count": n(128, "128 VLAN groups; configurable VID 1-4094"),
            "operating_temperature_c": t("-5 to 50 °C", "Operating temperature: -5 to 50 °C (23 to 122 °F)"),
            "dimensions_mm": t(
                "440 x 250 x 44 mm (L x W x H)",
                "DXS-1100-16SC dimensions (L x W x H): 440 x 250 x 44 mm",
            ),
            "max_power_consumption_w": n(60, "DXS-1100-16SC maximum power consumption: 60.0 W"),
            "power_supply": t("Internal 100-240 V AC", "Power input: 100 to 240 V AC"),
            "management_methods": t(
                "Web GUI, D-Link Network Assistant, SNMP v1/v2c/v3 and RMON v1/v2",
                "Management: Web-based GUI, D-Link Network Assistant Utility, SNMP v1/v2c/v3, SNMP trap and RMON v1/v2",
            ),
            "stp_features": t("IEEE 802.1D STP and 802.1w RSTP", "Spanning Tree Protocol: 802.1D STP and 802.1w RSTP"),
            "l2_features": t(
                "IGMP v1/v2 and MLD v1/v2 snooping, LLDP/LLDP-MED, STP/RSTP, 802.3x flow control, port mirroring, 802.1AX/802.3ad link aggregation, loopback detection and 9,216-byte jumbo frames",
                "L2 features include IGMP/MLD snooping, LLDP/LLDP-MED, STP/RSTP, flow control, port mirroring, link aggregation, jumbo frame and loopback detection",
            ),
            "acl_security": t(
                "D-Link Safeguard Engine, traffic segmentation, SSL v1/v2/v3, ARP spoofing and DoS prevention, port security and management-access authentication",
                "Security: storm control, D-Link Safeguard Engine, traffic segmentation, SSL v1/v2/v3, ARP spoofing prevention, DoS prevention, port security and AAA for management access",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import official D-Link DXS-1100-16SC performance, 9K jumbo-frame, VLAN and physical specifications."
    products = PRODUCTS
    document_version = "Updated June 2016, hardware A1; newest official series data sheet located, accessed 2026-10-22"
    brand_name = "D-Link"

