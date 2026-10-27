from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = "https://www.hpe.com/us/en/collaterals/collateral.a00029141enw.html"
TITLE = "HPE Aruba Networking CX 8320 Switch Series QuickSpecs, version 36"


PRODUCTS = {
    "CX 8320 JL479A": {
        "url": URL,
        "page": "Standard Features and JL479A Technical Specifications",
        "title": TITLE,
        "values": {
            "dimensions_mm": t("442 x 505.5 x 43.2 mm (W x D x H)"),
            "fanless": b(False, "Bundle includes five field-replaceable hot-swappable fans"),
            "fan_design": t("5 field-replaceable hot-swappable fans; front-to-back airflow"),
            "power_supply": t("2 field-replaceable hot-swappable power supplies included"),
            "redundant_power": b(True, "Two redundant, load-sharing, hot-swappable power supplies"),
            "max_power_consumption_w": n(357, "Electrical characteristics list power output as 357 W"),
            "operating_temperature_c": t("0 to 40 °C up to 10,000 ft"),
            "jumbo_frame_bytes": n(9000, "Maximum frame size: 9K bytes"),
            "igmp_group_capacity": t("4,094 IGMP groups"),
            "mld_snooping": b(True, "MLDv1 and MLDv2 are supported; table capacity is 4,094 MLD groups"),
            "vlan_count": n(4040, "Supports up to 4,040 port-based or IEEE 802.1Q VLANs"),
            "l2_features": t(
                "802.1Q VLAN; VLAN translation; STP/RSTP/MSTP/RPVST+; IGMP/MLD; port mirroring; "
                "LACP; loopback detection"
            ),
            "stp_features": t("IEEE 802.1D STP, 802.1w RSTP, 802.1s MSTP and RPVST+"),
            "lag_group_capacity": t("Up to 54 LAGs with 16 members per LAG"),
            "dhcp_features": t("IPv4/IPv6 DHCP server, client, relay and smart relay"),
            "routing_entry_capacity": t("131,072 IPv4 unicast routes; 32,732 IPv6 unicast routes"),
            "ospf_support": b(True, "OSPFv2 and OSPFv3 supported"),
            "rip_support": b(True, "RIPv2 and RIPng supported"),
            "pbr_support": b(True, "Policy-Based Routing supported"),
            "sdn_support": b(True, "AOS-CX provides built-in REST APIs and Python automation"),
            "stacking": t("Virtual Switching Extension (VSX) active-active two-switch architecture"),
            "stacking_units": n(2, "VSX high availability is delivered by deploying two chassis"),
            "management_methods": t(
                "AOS-CX CLI and REST APIs; SNMP; CX Mobile App; NetEdit; Network Analytics Engine; "
                "RJ45 serial, USB micro-B console and RJ45 Ethernet management port"
            ),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE Aruba Networking CX 8320 JL479A specifications."
    products = PRODUCTS
    document_version = "Official HPE QuickSpecs version 36 (2026-01-05); accessed 2026-10-16"
