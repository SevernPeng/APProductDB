from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/HPE%2BOfficeConnect%2B1920%2BSwitch%2BSeries-"
    "c04394247.pdf?contentDisposition=attachment&form=false&hf=regular&id=c04394247.pdf&"
    "isFutureVersion=true&isLinearized=false&preview=false&ver=8"
)
TITLE = "HPE OfficeConnect 1920 Switch Series QuickSpecs, version 8"


def shared_values():
    return {
        "cpu": t("MIPS at 500 MHz"),
        "flash_memory": t("32 MB flash"),
        "dram_memory": t("128 MB SDRAM"),
        "packet_buffer_mb": n(0.5, "512 KB packet buffer"),
        "jumbo_frame_bytes": n(10240, "Supports up to 10 kilobyte frame size"),
        "vlan_count": n(4094, "Supports 4,094 simultaneous VLAN IDs"),
        "l2_features": t("IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP; BPDU filtering; 802.1Q VLAN"),
        "l3_features": t("Basic IPv4/IPv6 static routing; up to 32 static routes and 8 VLAN interfaces"),
        "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP and IEEE 802.1s MSTP; BPDU filtering"),
        "routing_entry_capacity": t("32 IPv4 entries and 32 IPv6 entries"),
        "ip_interface_capacity": t("8 virtual VLAN interfaces"),
        "management_methods": t("HPE IMC; limited CLI; web browser; SNMP Manager"),
        "acl_security": t(
            "MAC-, IPv4- and IPv6-based ACLs including time-based ACLs; 802.1X and RADIUS; "
            "port isolation and port security; ARP attack protection; automatic DoS protection; HTTPS/SSL"
        ),
        "console_interfaces": t("1 x RJ45 limited-CLI console port"),
        "operating_temperature_c": t("0 to 40 °C"),
        "power_supply": t("Internal power supply, 100-240 V AC, 50/60 Hz"),
    }


def values(**specific):
    result = shared_values()
    result.update(specific)
    return result


PRODUCTS = {
    "1920 16G Switch": {
        "url": URL,
        "page": "pp. 4-5 and 13-14, JG923A",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("16 x 10/100/1000BASE-T RJ45 and 4 x 100/1000 Mbps SFP"),
            uplink_interfaces=t("4 x 100/1000 Mbps SFP"),
            dimensions_mm=t("440 x 173 x 44 mm (W x D x H)"),
            packet_forwarding_rate_mpps=n(29.8),
            switching_capacity_gbps=n(40),
            mac_address_table=t("8,192 entries"),
            max_power_consumption_w=n(13),
            fanless=b(True, "Acoustic specification: No Fan"),
            fan_design=t("Fanless"),
        ),
    },
    "1920 8G PoE+ (65W) switch": {
        "url": URL,
        "page": "pp. 4-5 and 11-12, JG921A",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("8 x 10/100/1000BASE-T PoE+ RJ45 and 2 x 100/1000 Mbps SFP"),
            uplink_interfaces=t("2 x 100/1000 Mbps SFP"),
            dimensions_mm=t("330 x 230 x 44 mm (W x D x H)"),
            packet_forwarding_rate_mpps=n(14.8),
            switching_capacity_gbps=n(20),
            mac_address_table=t("8,192 entries"),
            max_power_consumption_w=n(94),
            fanless=b(True, "Acoustic pressure 0 dB; no fan"),
            fan_design=t("Fanless"),
            poe_ports=n(8),
            poe_budget_w=n(65),
            max_poe_per_port_w=n(30, "PoE+ supplies up to 30 W per port"),
            poe_standard=t("IEEE 802.3af / 802.3at PoE+"),
            poe_configuration=t("8 x Gigabit PoE+ ports; 65 W total budget"),
        ),
    },
    "1920 8G PoE+ (180W) switch": {
        "url": URL,
        "page": "pp. 4-5 and 12-13, JG922A",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("8 x 10/100/1000BASE-T PoE+ RJ45 and 2 x 100/1000 Mbps SFP"),
            uplink_interfaces=t("2 x 100/1000 Mbps SFP"),
            dimensions_mm=t("330 x 230 x 44 mm (W x D x H)"),
            packet_forwarding_rate_mpps=n(14.8),
            switching_capacity_gbps=n(20),
            mac_address_table=t("8,192 entries"),
            max_power_consumption_w=n(235),
            fanless=b(False, "Low-speed fan 43.6 dB; high-speed fan 51.5 dB"),
            fan_design=t("Variable-speed fan; 43.6 dB low / 51.5 dB high"),
            poe_ports=n(8),
            poe_budget_w=n(180),
            max_poe_per_port_w=n(30, "PoE+ supplies up to 30 W per port"),
            poe_standard=t("IEEE 802.3af / 802.3at PoE+"),
            poe_configuration=t("8 x Gigabit PoE+ ports; 180 W total budget"),
        ),
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE OfficeConnect 1920 switch specifications."
    products = PRODUCTS
    document_version = "Official retired HPE QuickSpecs version 8; accessed 2026-10-16"
