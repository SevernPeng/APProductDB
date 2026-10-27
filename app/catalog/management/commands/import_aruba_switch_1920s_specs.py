from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    n,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/HPE%20OfficeConnect%201920S%20Switch%20Series-"
    "a00001630enw.pdf?contentDisposition=attachment&form=false&hf=regular&id=a00001630enw.pdf&"
    "isFutureVersion=true&isLinearized=false&preview=false&ver=4"
)
TITLE = "HPE OfficeConnect 1920S Switch Series QuickSpecs, version 4"


def shared_values():
    return {
        "cpu": t("ARM Cortex-A9 at 400 MHz"),
        "dram_memory": t("256 MB SDRAM"),
        "flash_memory": t("64 MB flash; dual flash images supported"),
        "packet_buffer_mb": n(1.5),
        "jumbo_frame_bytes": n(9216),
        "vlan_count": n(256, "256 VLANs; VLAN ID range 2-4093"),
        "l2_features": t(
            "IEEE 802.1D STP, 802.1w RSTP and 802.1s MSTP; BPDU filtering; 802.1Q VLAN; "
            "LACP; IGMP snooping; loop protection"
        ),
        "l3_features": t("Static IPv4 routing with up to 32 routes; ARP and DHCP relay"),
        "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP and IEEE 802.1s MSTP; BPDU filtering"),
        "routing_entry_capacity": t("32 static IPv4 routes"),
        "management_methods": t("Web GUI over HTTP/HTTPS; SNMPv1/v2c/v3; RMON; FTP/TFTP"),
        "acl_security": t(
            "Up to 50 inbound IPv4/MAC ACL entries; RADIUS and 802.1X; port isolation; "
            "automatic denial-of-service protection; HTTPS/SSL management"
        ),
        "dhcp_features": t("Default DHCP client mode and DHCP relay"),
        "lag_group_capacity": t("4 trunks on 8-port models; maximum 8 ports per trunk"),
        "operating_temperature_c": t("0 to 40 °C"),
        "fanless": b(True, "Acoustic power 0 dB; no fan"),
        "fan_design": t("Fanless"),
    }


def values(**specific):
    result = shared_values()
    result.update(specific)
    return result


PRODUCTS = {
    "1920S 8G Switch": {
        "url": URL,
        "page": "pp. 1-5 and 11-12, JL380A",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("8 x 10/100/1000BASE-T RJ45"),
            dimensions_mm=t("254 x 159.5 x 43.9 mm (W x D x H)"),
            packet_forwarding_rate_mpps=n(11.9),
            switching_capacity_gbps=n(16),
            mac_address_table=t("8,000 entries"),
            max_power_consumption_w=n(9.5),
            power_supply=t("100-240 V AC; may alternatively be powered by an upstream PoE switch"),
        ),
    },
    "1920S 8G PPoE+ 65W Switch": {
        "url": URL,
        "page": "pp. 1-5 and 14-15, JL383A",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("4 x 10/100/1000BASE-T PoE+ RJ45 and 4 x 10/100/1000BASE-T RJ45"),
            dimensions_mm=t("254 x 159.5 x 43.9 mm (W x D x H)"),
            packet_forwarding_rate_mpps=n(11.9),
            switching_capacity_gbps=n(16),
            mac_address_table=t("8,000 entries"),
            max_power_consumption_w=n(72.9),
            power_supply=t("Internal power supply, 100-240 V AC, 50/60 Hz"),
            poe_ports=n(4),
            poe_budget_w=n(65),
            max_poe_per_port_w=n(30),
            poe_standard=t("IEEE 802.3af / 802.3at PoE+"),
            poe_configuration=t("Ports 1-4 support PoE/PoE+; 65 W total budget"),
        ),
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified HPE OfficeConnect 1920S switch specifications."
    products = PRODUCTS
    document_version = "Official retired HPE QuickSpecs version 4; accessed 2026-10-16"
