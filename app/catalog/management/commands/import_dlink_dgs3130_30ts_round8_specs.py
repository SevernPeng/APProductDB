from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)


DS = "https://support.dlink.com/resource/products/dgs-3130-series/REVB/DGS-3130-SERIES_REVB_DATASHEET_V1.21_WW.pdf"


PRODUCTS = {
    "DGS-3130-30TS": {
        "url": DS,
        "page": "pp. 3-7, Revision B performance, physical, VLAN, ACL and L3 routing specifications",
        "title": "D-Link DGS-3130 Series Layer 3 Stackable Managed Switches Data Sheet v1.21 WW",
        "values": {
            "vlan_count": n(4096, "Maximum 4K VLAN groups; maximum VIDs 1-4094"),
            "operating_temperature_c": t("0 to 50 °C", "Operation temperature: 0 to 50 °C (32 to 122 °F)"),
            "acl_security": t(
                "ACLs based on 802.1p, VID, MAC, EtherType, LLC, VLAN, IPv4/IPv6, DSCP, protocol and TCP/UDP ports; 2,048 ingress and 512 egress hardware entries; 802.1X, DHCP snooping, IP source guard, DAI, IPv6 guards, SSH and TLS",
                "ACL: maximum 2048 ingress and 512 egress hardware entries, with L2-L4 and IPv6 classifiers; security includes 802.1X, DHCP snooping, source guards, DAI, SSH and TLS",
            ),
            "ip_interface_capacity": t("128 IP interfaces", "IP Interface: supports 128 interfaces"),
            "routing_entry_capacity": t(
                "1,024 shared IPv4/IPv6 hardware routing entries; up to 4,096 shared L3 forwarding entries; 512 IPv4 and 256 IPv6 static routes",
                "Supports 1024 hardware routing entries shared by IPv4/IPv6 and up to 4096 shared hardware L3 forwarding entries; max. 512 IPv4 and 256 IPv6 static routes",
            ),
            "ospf_support": b(True, "OSPF v2/v3, passive interface, Stub/NSSA area and ECMP"),
            "rip_support": b(True, "RIPv1/v2/ng"),
            "pbr_support": b(True, "PBR (Policy-based Route)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import current D-Link DGS-3130-30TS Revision B VLAN, ACL and L3 routing specifications."
    products = PRODUCTS
    document_version = "Revision B v1.21 WW, ©2022 D-Link; accessed 2026-10-22"
    brand_name = "D-Link"

