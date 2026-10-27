from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%202530%20Switch%20Series-"
    "c04111414.pdf?contentDisposition=attachment&form=false&hf=regular&id=c04111414.pdf&"
    "isFutureVersion=true&isLinearized=false&preview=false&servePdfFile=true&ver=13"
)
TITLE = "HPE Aruba Networking 2530 Switch Series QuickSpecs, version 13"


def shared_values():
    return {
        "cpu": t("ARM9E at 800 MHz"),
        "flash_memory": t("128 MB flash"),
        "dram_memory": t("256 MB DDR3 DIMM"),
        "jumbo_frame_bytes": n(9220, "Gigabit models support frames up to 9,220 bytes"),
        "vlan_count": n(512, "Supports 512 VLANs and 4,094 VLAN IDs"),
        "l2_features": t(
            "VLANs; GVRP; RPVST+; IEEE 802.1D/802.1w/802.1s spanning tree; LACP; "
            "SmartLink; 16K MAC table"
        ),
        "stp_features": t("RPVST+; IEEE 802.1s MSTP with legacy IEEE 802.1D and 802.1w support"),
        "acl_security": t(
            "IPv4/IPv6 port- and VLAN-based ACLs; source-port filtering; 802.1X, web and MAC authentication; "
            "RADIUS/TACACS+; port security"
        ),
        "management_methods": t(
            "HPE IMC; command-line interface; web browser; configuration menu; SNMP; "
            "out-of-band serial console"
        ),
        "console_interfaces": t("1 dual-personality RJ45 or USB micro-B serial console port"),
        "operating_temperature_c": t("0 to 45 °C"),
        "power_supply": t("Power supply included"),
    }


def values(**specific):
    result = shared_values()
    result.update(specific)
    return result


PRODUCTS = {
    "2530-48G-PoE+ Switch": {
        "url": URL,
        "page": "pp. 22-23, J9772A technical specifications",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T PoE+ RJ45 and 4 x fixed Gigabit SFP"),
            uplink_interfaces=t("4 x fixed Gigabit Ethernet SFP"),
            dimensions_mm=t("443 x 322.6 x 44.5 mm (W x D x H)"),
            packet_buffer_mb=n(3),
            packet_forwarding_rate_mpps=n(77.3),
            switching_capacity_gbps=n(104),
            max_power_consumption_w=n(476),
            fanless=b(False, "Acoustic power 43.6 dB and pressure 33.6 dB"),
            fan_design=t("Active cooling; acoustic power 43.6 dB"),
            poe_ports=n(48),
            poe_budget_w=n(382),
            max_poe_per_port_w=n(30, "Up to 30 W per IEEE 802.3at PoE+ port"),
            poe_standard=t("IEEE 802.3af / 802.3at PoE+"),
            poe_configuration=t("48 x Gigabit PoE+ ports; 382 W total budget"),
        ),
    },
    "2530-24G-PoE+ Switch": {
        "url": URL,
        "page": "pp. 23-24, J9773A technical specifications",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T PoE+ RJ45 and 4 x fixed Gigabit SFP"),
            uplink_interfaces=t("4 x fixed Gigabit Ethernet SFP"),
            dimensions_mm=t("443 x 330.2 x 44.5 mm (W x D x H)"),
            packet_buffer_mb=n(1.5),
            packet_forwarding_rate_mpps=n(41.6),
            switching_capacity_gbps=n(56),
            max_power_consumption_w=n(247),
            fanless=b(False, "Acoustic power 43.9 dB and pressure 39.6 dB"),
            fan_design=t("Active cooling; acoustic power 43.9 dB"),
            poe_ports=n(24),
            poe_budget_w=n(195),
            max_poe_per_port_w=n(30, "Up to 30 W per IEEE 802.3at PoE+ port"),
            poe_standard=t("IEEE 802.3af / 802.3at PoE+"),
            poe_configuration=t("24 x Gigabit PoE+ ports; 195 W total budget"),
        ),
    },
    "2530-48G Switch": {
        "url": URL,
        "page": "pp. 31-32, J9775A technical specifications",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T RJ45 and 4 x fixed Gigabit SFP"),
            uplink_interfaces=t("4 x fixed Gigabit Ethernet SFP"),
            dimensions_mm=t("443 x 254 x 44.5 mm (W x D x H)"),
            packet_buffer_mb=n(3),
            packet_forwarding_rate_mpps=n(77.3),
            switching_capacity_gbps=n(104),
            max_power_consumption_w=n(59.5),
            fanless=b(False, "Acoustic power 34.5 dB and pressure 31.0 dB"),
            fan_design=t("Active cooling; acoustic power 34.5 dB"),
        ),
    },
    "2530-24G Switch": {
        "url": URL,
        "page": "pp. 32-34, J9776A technical specifications",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T RJ45 and 4 x fixed Gigabit SFP"),
            uplink_interfaces=t("4 x fixed Gigabit Ethernet SFP"),
            dimensions_mm=t("443 x 254 x 44.5 mm (W x D x H)"),
            packet_buffer_mb=n(1.5),
            packet_forwarding_rate_mpps=n(41.6),
            switching_capacity_gbps=n(56),
            max_power_consumption_w=n(48),
            fanless=b(False, "Acoustic power 34.0 dB and pressure 26.4 dB"),
            fan_design=t("Active cooling; acoustic power 34.0 dB"),
        ),
    },
    "2530-8G Switch": {
        "url": URL,
        "page": "pp. 34-35, J9777A technical specifications",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t(
                "8 x 10/100/1000BASE-T RJ45 plus 2 dual-personality ports, each usable as Gigabit RJ45 or SFP"
            ),
            uplink_interfaces=t("2 x dual-personality Gigabit RJ45/SFP ports"),
            dimensions_mm=t("254 x 159.5 x 44.5 mm (W x D x H)"),
            packet_buffer_mb=n(1.5),
            packet_forwarding_rate_mpps=n(14.8),
            switching_capacity_gbps=n(20),
            max_power_consumption_w=n(18.6),
            fanless=b(True, "Acoustic power and pressure are both specified as 0 dB"),
            fan_design=t("Fanless"),
        ),
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified Aruba 2530 switch specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking QuickSpecs version 13; accessed 2026-10-16"
