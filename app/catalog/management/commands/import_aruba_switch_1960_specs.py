from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = "https://www.hpe.com/us/en/collaterals/collateral.a50002593enw.html"
TITLE = "HPE Networking Instant On Switch 1960 QuickSpecs"


def shared_values():
    return {
        "vlan_count": n(256, "Access switch models support up to 256 VLANs"),
        "jumbo_frame_bytes": n(9216, "Supports up to 9216 bytes frame size"),
        "l2_features": t(
            "802.1D STP, 802.1w RSTP, 802.1s MSTP; IGMP v1/v2/v3 and MLD v1/v2 snooping; "
            "LACP; LLDP/LLDP-MED; VLAN; port mirroring; loop protection"
        ),
        "l3_features": t("Static IPv4/IPv6 routing; DHCP relay; ARP table"),
        "stacking": t(
            "True stacking and cloud-managed stacking; ring or chain topology; access and aggregation "
            "models may be mixed"
        ),
        "stacking_units": n(4, "Up to four 1960 switches per stack"),
        "management_methods": t(
            "Instant On cloud-hosted web portal and mobile app; local web GUI; SNMPv1/v2c/v3"
        ),
        "stp_features": t("IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP"),
        "mld_snooping": b(True, "MLDv1 and MLDv2 snooping supported"),
        "dhcp_features": t("DHCP client, DHCP relay, IPv6 DHCP relay and IPv4 DHCP server"),
        "lag_group_capacity": t("Up to 16 trunks, maximum 8 ports per trunk"),
        "ip_interface_capacity": t("8 VLAN routing interfaces on access switch models"),
        "routing_entry_capacity": t("32 IPv4/IPv6 static entries"),
        "operating_temperature_c": t("0 to 40 °C"),
        "uplink_interfaces": t("2 x 10GBASE-T RJ45 and 2 x 10GbE SFP+"),
    }


def values(**specific):
    result = shared_values()
    result.update(specific)
    return result


PRODUCTS = {
    "1960 24G 2XGT 2SFP+ Switch (JL806A)": {
        "url": URL,
        "page": "Standard Features and JL806A Specifications",
        "title": TITLE,
        "values": values(
            dimensions_mm=t("350.5 x 442.5 x 43.95 mm (D x W x H)"),
            packet_forwarding_rate_mpps=n(95),
            switching_capacity_gbps=n(128),
            max_power_consumption_w=n(80, "Maximum power rating: 60 W at 100-127 V; 80 W at 200-220 V"),
            fanless=b(True, "24-port non-PoE model has a fan-less design"),
            fan_design=t("Fanless"),
        ),
    },
    "1960 (JL807A)": {
        "url": URL,
        "page": "Standard Features and JL807A Specifications",
        "title": TITLE,
        "values": values(
            dimensions_mm=t("350.5 x 442.5 x 43.95 mm (D x W x H)"),
            packet_forwarding_rate_mpps=n(95),
            switching_capacity_gbps=n(128),
            max_power_consumption_w=n(500, "Maximum power rating: 500 W at 100-127 V; 480 W at 200-220 V"),
            fanless=b(False, "PoE model uses energy-efficient variable-speed fan cooling"),
            fan_design=t("Variable-speed fan cooling"),
            poe_ports=n(24, "24 PoE ports: 20 Class 4 and 4 Class 6"),
            poe_budget_w=n(370, "370 W total PoE power"),
            max_poe_per_port_w=n(60, "Up to 60 W on Class 6 PoE ports"),
            poe_standard=t("IEEE 802.3af / 802.3at Class 4 / 802.3bt Class 6"),
            poe_configuration=t("20 x Class 4 PoE ports and 4 x Class 6 PoE ports"),
        ),
    },
    "1960 48G 2XGT 2SFP+ Switch (JL808A)": {
        "url": URL,
        "page": "Standard Features and JL808A Specifications",
        "title": TITLE,
        "values": values(
            dimensions_mm=t("350.5 x 442.5 x 43.95 mm (D x W x H)"),
            packet_forwarding_rate_mpps=n(131),
            switching_capacity_gbps=n(176),
            max_power_consumption_w=n(120, "Maximum power rating: 110 W at 100-127 V; 120 W at 200-220 V"),
            fanless=b(False, "Model has measured acoustic output and uses variable-speed fan cooling"),
            fan_design=t("Variable-speed fan cooling"),
        ),
    },
    "1960 Switch (JL809A)": {
        "url": URL,
        "page": "Standard Features and JL809A Specifications",
        "title": TITLE,
        "values": values(
            dimensions_mm=t("402.75 x 442.5 x 43.95 mm (D x W x H)"),
            packet_forwarding_rate_mpps=n(131),
            switching_capacity_gbps=n(176),
            max_power_consumption_w=n(790, "Maximum power rating: 790 W at 100-127 V; 760 W at 200-220 V"),
            fanless=b(False, "PoE model uses energy-efficient variable-speed fan cooling"),
            fan_design=t("Variable-speed fan cooling"),
            poe_ports=n(48, "48 PoE ports: 40 Class 4 and 8 Class 6"),
            poe_budget_w=n(600, "600 W total PoE power"),
            max_poe_per_port_w=n(60, "Up to 60 W on Class 6 PoE ports"),
            poe_standard=t("IEEE 802.3af / 802.3at Class 4 / 802.3bt Class 6"),
            poe_configuration=t("40 x Class 4 PoE ports and 8 x Class 6 PoE ports"),
        ),
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE Networking Instant On 1960 switch specifications."
    products = PRODUCTS
    document_version = "Current official HPE QuickSpecs HTML; accessed 2026-10-16"
