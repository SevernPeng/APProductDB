from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "DXS-3610": {
        "url": "https://www.dlink.com/en/-/media/business_products/dxs/dxs-3610/datasheet/dxs3610seriesa1datasheetv104ww.pdf",
        "version": "A1 v1.04 WW",
        "title": "D-Link DXS-3610 Series Layer 3 Stackable 10G Managed Switches Datasheet",
    },
    "DXS-3400": {
        "url": "https://www.dlink.com/en/-/media/business_products/dxs/dxs-3400-24sc/datasheet/dxs3400seriesdatasheet801ww.pdf",
        "version": "v8.01 WW",
        "title": "D-Link DXS-3400 Series Lite Layer 3 Stackable 10 GbE Managed Switches Datasheet",
    },
}


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


DXS_3610_COMMON = {
    "switching_capacity_gbps": n(2160),
    "packet_forwarding_rate_mpps": n(1607.04),
    "mac_address_table": t("Up to 288K entries (resource-profile dependent)"),
    "packet_buffer_mb": n(32),
    "jumbo_frame_bytes": n(9436),
    "power_supply": t("1+1 redundant hot-swappable power supplies; 100-240 V AC, 50/60 Hz"),
    "fan_design": t("5 hot-swappable fans; N+1 cooling redundancy; front-to-back airflow"),
    "management_methods": t("Web GUI; CLI; SNMP v1/v2c/v3; Telnet; D-Link Network Assistant; sFlow; RMON; out-of-band management"),
    "vlan_count": n(4094),
    "l2_features": t("802.1AX link aggregation; MLAG; ERPS; RSPAN; L2 protocol tunneling; IGMP/MLD snooping"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; Root Restriction"),
    "acl_security": t("MAC/IPv4/IPv6 ACLs; 2304 ingress and 2K egress rules; 802.1X; DHCP snooping; DAI; IP Source Guard"),
    "ip_interface_capacity": t("256 IP interfaces"),
    "routing_entry_capacity": t("Up to 32K IPv4 / 16K IPv6 routes; up to 144K IPv4 / 144K IPv6 forwarding entries, resource-profile dependent"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "stacking": t("Physical ring/chain stacking up to 12 switches; virtual stacking/clustering up to 32 units"),
    "stacking_bandwidth_gbps": n(1200),
    "stacking_units": n(12),
    "max_power_consumption_w": n(320.8),
    "dimensions_mm": t("441 x 487.44 x 43.5 mm"),
    "operating_temperature_c": t("0 to 45 °C"),
}

DXS_3400_COMMON = {
    "switching_capacity_gbps": n(480),
    "packet_forwarding_rate_mpps": n(357.12),
    "mac_address_table": t("Up to 48K entries"),
    "packet_buffer_mb": n(4),
    "jumbo_frame_bytes": n(12288),
    "power_supply": t("Modular hot-swappable AC/DC power supplies; 100-240 V AC, 50/60 Hz; 1+1 redundancy supported"),
    "fan_design": t("3 hot-swappable fan modules; N+1 cooling redundancy; front-to-back airflow"),
    "management_methods": t("Web GUI; CLI; SNMP v1/v2c/v3; Telnet; SFTP; sFlow; RMON; out-of-band management"),
    "vlan_count": n(4094),
    "l2_features": t("802.1AX link aggregation; MLAG; ERPS; port/flow/VLAN mirroring; L2 protocol tunneling; IGMP/MLD snooping"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; Root Guard; Loop Guard"),
    "acl_security": t("MAC/IPv4/IPv6 ACLs; 1792 IPv4 / 448 IPv6 ingress and 512 IPv4 / 256 IPv6 egress entries; 802.1X; DHCP snooping; DAI; IP Source Guard"),
    "ip_interface_capacity": t("256 IP interfaces"),
    "routing_entry_capacity": t("4096 shared IPv4/IPv6 hardware routes; up to 32K IPv4 / 16K IPv6 forwarding entries"),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "stacking": t("Physical ring/chain stacking up to 4 switches; virtual stacking/clustering up to 32 units"),
    "stacking_bandwidth_gbps": n(80),
    "stacking_units": n(4),
    "max_power_consumption_w": n(118.6),
    "dimensions_mm": t("441 x 380 x 44 mm"),
    "operating_temperature_c": t("-5 to 50 °C"),
}


MODELS = {
    "DXS-3610-54S": {
        "family": "DXS-3610",
        "location": "Technical Specifications pp. 3-6; current product family page",
        "note": "Official current A1 v1.04 datasheet; hardware-family capability shown on the unsuffixed product record, with enhanced-image-only L3 multicast called out in the value text.",
        "values": {
            **DXS_3610_COMMON,
            "l3_features": t("IPv4/IPv6 static routing; RIP/RIPng; OSPFv2/v3; PBR; VRRP; BFD; enhanced image adds BGP, IS-IS and L3 multicast"),
            "multicast_routing": b(),
        },
    },
    "DXS-3610-54S/SI": {
        "family": "DXS-3610",
        "location": "Standard Image (SI) Features pp. 4-6",
        "note": "Official current A1 v1.04 datasheet; values restricted to Standard Image capability. L3 multicast is an Enhanced Image addition.",
        "values": {
            **DXS_3610_COMMON,
            "l3_features": t("Standard Image: IPv4/IPv6 static routing; RIP/RIPng; OSPFv2/v3; PBR; VRRP; BFD"),
            "multicast_routing": b(False),
        },
    },
    "DXS-3400-24SC": {
        "family": "DXS-3400",
        "location": "Technical Specifications and Standard Image Software Features pp. 2-5",
        "note": "Official v8.01 WW datasheet; unsuffixed/base record is treated as Standard Image. OSPF and L3 multicast are Enhanced Image additions.",
        "values": {
            **DXS_3400_COMMON,
            "l3_features": t("Standard Image: IPv4/IPv6 static routing; RIP/RIPng; PBR; VRRP; BFD"),
            "ospf_support": b(False),
            "multicast_routing": b(False),
        },
    },
    "DXS-3400-24SC/EI": {
        "family": "DXS-3400",
        "location": "Technical Specifications pp. 2-5; Enhanced Image Software Features p. 5",
        "note": "Official v8.01 WW datasheet; /EI includes all Standard Image features plus OSPF and L3 multicast.",
        "values": {
            **DXS_3400_COMMON,
            "l3_features": t("Enhanced Image: IPv4/IPv6 static routing; RIP/RIPng; PBR; VRRP; BFD; OSPFv2/v3; GRE/ISATAP/6to4; L3 multicast"),
            "ospf_support": b(),
            "multicast_routing": b(),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DXS-3610 and DXS-3400 specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")
        codes = {code for model in MODELS.values() for code in model["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        documents = {}
        for family, source_data in SOURCES.items():
            documents[family], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"],
                document_version=source_data["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": source_data["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = 0
        missing_models = []
        for model, model_data in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source_data = SOURCES[model_data["family"]]
            source = documents[model_data["family"]]
            for code, (kind, data) in model_data["values"].items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": source_data["url"][:200],
                    "source_note": model_data["note"],
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(data)
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=model_data["location"],
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
