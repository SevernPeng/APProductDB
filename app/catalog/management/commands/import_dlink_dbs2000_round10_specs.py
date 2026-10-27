from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


DS = "https://support.dlink.com/resource/products/DBS-2000-SERIES/REVA/DBS-2000-SERIES_REVA_DATASHEET_v1.03_US.pdf"


COMMON = {
    "poe_standard": t("IEEE 802.3af/at PoE/PoE+", "PoE models comply with IEEE 802.3af/at and provide up to 30 W per port"),
    "max_poe_per_port_w": n(30, "30 W maximum per port"),
    "packet_buffer_mb": n(0.512, "Packet buffer: 4.1 Mbits (normalized to 0.512 MB at database precision)"),
    "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply", "Power input: 100 to 240 V AC, 50/60 Hz internal power supply"),
    "operating_temperature_c": t("-5 to 50 °C", "Operating temperature: -5 to 50 °C (23 to 122 °F)"),
    "vlan_count": n(256, "Supports 256 static VLAN groups"),
    "l2_features": t(
        "802.1Q tagged, management, voice and guest VLAN; port mirroring; jumbo frames; IGMP v1/v2/v3 snooping (256 groups); cable diagnostics; LLDP; 802.3ad link aggregation; loopback detection",
        "L2 features include port mirroring, jumbo frames, IGMP v1/v2/v3 awareness snooping, cable diagnostics, LLDP, 802.3ad link aggregation and loopback detection",
    ),
    "stp_features": t("IEEE 802.1w RSTP", "Supports IEEE 802.1w Rapid Spanning Tree (RSTP)"),
    "acl_security": t(
        "Ingress ACL with up to 768 entries; SSL; DHCP Server Screening; 802.1X port/MAC-based authentication",
        "Security features: SSL, DHCP Server Screening, 802.1X port/MAC-based authentication and ACL with a maximum of 768 entries",
    ),
    "management_methods": t(
        "Nuclias Cloud browser platform and Nuclias mobile app; zero-touch deployment",
        "Management: Cloud-based through Nuclias and Nuclias mobile app",
    ),
}


PRODUCTS = {
    "DBS-2000-10MP": {
        "url": DS,
        "page": "pp. 4-6, DBS-2000-10MP column and common software features",
        "title": "D-Link DBS-2000 Series Nuclias Cloud-Managed Switches Datasheet v1.03 US",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(20, "Switching capacity: 20 Gbps"),
            "packet_forwarding_rate_mpps": n(14.88, "Maximum forwarding rate: 14.88 Mpps"),
            "poe_ports": n(8, "PoE capable ports: ports 1 to 8"),
            "poe_budget_w": n(130, "PoE power budget: 130 W"),
            "max_power_consumption_w": n(152.3, "Maximum power consumption: 152.3 W with PoE on; 9.4 W with PoE off"),
            "dimensions_mm": t("330 x 180 x 44 mm", "Dimensions: 330 x 180 x 44 mm"),
            "fan_design": t("Fanless", "Ventilation: Fanless"),
        },
    },
    "DBS-2000-28P": {
        "url": DS,
        "page": "pp. 4-6, DBS-2000-28P column and common software features",
        "title": "D-Link DBS-2000 Series Nuclias Cloud-Managed Switches Datasheet v1.03 US",
        "values": {
            **COMMON,
            "switching_capacity_gbps": n(56, "Switching capacity: 56 Gbps"),
            "packet_forwarding_rate_mpps": n(41.7, "Maximum forwarding rate: 41.7 Mpps"),
            "poe_ports": n(24, "PoE capable ports: ports 1 to 24"),
            "poe_budget_w": n(193, "PoE power budget: 193 W"),
            "max_power_consumption_w": n(263.9, "Maximum power consumption: 263.9 W with PoE on; 30.6 W with PoE off"),
            "dimensions_mm": t("440 x 250 x 44 mm", "Dimensions: 440 x 250 x 44 mm"),
            "fan_design": t("2 fans", "Ventilation: 2 x Fans"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import verified current D-Link DBS-2000-10MP/28P hardware and software specifications."
    products = PRODUCTS
    document_version = "Revision A v1.03 US; published 2026; accessed 2026-10-22"
    brand_name = "D-Link"
