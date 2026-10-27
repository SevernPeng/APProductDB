from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_M4300 = "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4300.pdf?cid=091917_insight_us_em"
URL_M4500 = "https://downloads1.netgear.com/files/netgear/documents/M4500.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


M4300_COMMON = {
    "jumbo_frame_bytes": n(9216, "Maximum 9K jumbo frame"),
    "mac_address_table": t("16K"),
    "vlan_count": n(4093),
    "management_methods": t(
        "Web GUI; industry-standard CLI; Telnet/SSH; SNMP v1/v2/v3; RMON; sFlow; NMS300"
    ),
    "l2_features": t(
        "IEEE 802.1Q; port-, protocol-, MAC- and subnet-based VLANs; LACP; IGMP/MLD snooping; "
        "MVR; QinQ; LLDP/LLDP-MED; port mirroring; QoS"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; PVSTP/PVRSTP; "
        "loop guard; root guard; BPDU guard"
    ),
    "acl_security": t(
        "100 MAC, IPv4 or IPv6 ACLs; up to 1,023 rules per ACL and 16K system-wide rules; "
        "L2/L3/L4 matching; 802.1X; DHCP snooping; IP source guard; dynamic ARP inspection"
    ),
    "l3_features": t(
        "IPv4/IPv6 static routing; policy-based routing; RIP; OSPF; VRRP; ECMP; PIM-SM/PIM-DM"
    ),
    "dhcp_features": t(
        "DHCP/BOOTP relay and server for IPv4/IPv6; DHCP snooping; DHCP client and auto-install"
    ),
    "pbr_support": b(True, "Policy-based routing supported"),
    "ospf_support": b(True, "OSPFv2 and OSPFv3 supported"),
    "rip_support": b(True, "RIPv1/RIPv2 and RIPng supported"),
    "vrrp_support": b(True, "VRRP supported"),
    "stacking": t("Virtual Chassis stacking using any 10G port; mixed M4300 stacking"),
    "stacking_units": n(8, "Up to 8 switches per stack"),
    "stacking_bandwidth_gbps": n(320, "Up to 320 Gbps stacking bandwidth"),
    "operating_temperature_c": t("0 to 50 °C"),
}


M4500_COMMON = {
    "packet_forwarding_rate_mpps": n(2000, "2 Bpps system throughput"),
    "packet_buffer_mb": n(32, "256 Mb packet buffer"),
    "jumbo_frame_bytes": n(9216, "Maximum 9K jumbo frame"),
    "vlan_count": n(4093),
    "vlan_support": t("IEEE 802.1Q tagged and port-based VLANs; up to 4,093 VLANs"),
    "lag_group_capacity": t("64 LAGs; up to 32 member ports per LAG"),
    "l2_features": t(
        "IEEE 802.1Q; LACP; MLAG; IGMP/MLD snooping; MVR; QinQ; LLDP/LLDP-MED; "
        "port mirroring; QoS"
    ),
    "stp_features": t(
        "IEEE 802.1w RSTP; IEEE 802.1s MSTP with 31 MST instances plus one CST; "
        "loop guard; root guard; BPDU filter/guard; automatic edge-port detection"
    ),
    "acl_security": t(
        "100 MAC, IPv4 or IPv6 ACLs; up to 1,023 configurable rules per ACL and 16,384 "
        "system-wide rules; L2/L3/L4 matching; 802.1X; DHCP snooping; IP source guard"
    ),
    "dhcp_features": t("BOOTP/DHCP relay agent; DHCP snooping"),
    "ospf_support": b(True, "OSPFv2 and OSPFv3 supported"),
    "pbr_support": b(True, "Policy-based routing supported"),
    "rip_support": b(False, "RIPv1/RIPv2: No"),
    "vrrp_support": b(True, "VRRP supported"),
    "operating_temperature_c": t("0 to 50 °C"),
}


PRODUCTS = {
    "M4300-24XF": {
        "url": URL_M4300,
        "title": "NETGEAR M4300 Intelligent Edge Series Fully Managed Switches datasheet",
        "page": "pp. 4-13, 20-29",
        "values": {
            **M4300_COMMON,
            "ethernet_interfaces": t(
                "24 x 1G/10G SFP+; 2 x 10GBASE-T RJ45 shared with SFP+ ports",
                "24 x SFP+ and 2 x 10GBASE-T shared back ports; 24 usable 10G ports",
            ),
            "uplink_interfaces": t(
                "Any 10G SFP+ or 10GBASE-T port can be used for uplink or stacking"
            ),
            "switching_capacity_gbps": n(480),
            "packet_forwarding_rate_mpps": n(357),
            "packet_buffer_mb": n(4, "32 Mb shared packet buffer"),
            "routing_entry_capacity": t("512 Layer 3 route-table entries"),
            "dimensions_mm": t("214.7 x 345 x 44 mm (W x D x H)"),
            "max_power_consumption_w": n(87.2),
            "power_supply": t("1 x APS250W modular PSU; one PSU slot; 110-240 V AC"),
            "fan_design": t("Active cooling; 39.7 dBA at 25 °C"),
        },
    },
    "M4500-32C": {
        "url": URL_M4500,
        "title": "NETGEAR M4500 Fully Managed Switches datasheet",
        "page": "pp. 5-13",
        "values": {
            **M4500_COMMON,
            "switching_capacity_gbps": n(6400, "6.4 Tbps switching fabric"),
        },
    },
    "M4500-48XF8C": {
        "url": URL_M4500,
        "title": "NETGEAR M4500 Fully Managed Switches datasheet",
        "page": "pp. 5-13",
        "values": {
            **M4500_COMMON,
            "switching_capacity_gbps": n(4000, "4 Tbps switching fabric"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR M4300 and M4500 switch specifications."
    document_version = "Official NETGEAR datasheet; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            if item["url"] in documents:
                continue
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=self.document_version,
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": item["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_status = existing.value_status if existing else None
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['page']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value))
                    defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value)
                    defaults["value_boolean"] = new_value
                else:
                    new_value = str(value)
                    defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1
                    model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"{item['page']} - {model} specifications - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
