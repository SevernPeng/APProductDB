from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.dlink.com/en/-/media/product-pages/dgs/3630/series/assets/dgs3630seriesdatasheetv804ww.pdf"
SOURCE_VERSION = "v8.04 WW"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "mac_address_table": t("68,000 entries"),
    "packet_buffer_mb": n(4),
    "jumbo_frame_bytes": n(12288),
    "power_supply": t("100-240 V AC, 50/60 Hz; optional redundant power supply"),
    "fan_design": t("2 smart fans"),
    "management_methods": t("Web GUI; CLI; SNMP; RMON; Telnet/SSH; out-of-band management port"),
    "vlan_count": n(4094),
    "l2_features": t("802.1AX link aggregation; ERPS v2; MLAG; port/RSPAN mirroring; L2 protocol tunneling; IGMP/MLD snooping"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; Root Guard; Loop Guard"),
    "acl_security": t("MAC/IPv4/IPv6 ACLs; 4K ingress and 1K egress hardware entries; 802.1X; DHCP snooping; DAI; IP Source Guard"),
    "l3_features": t("IPv4/IPv6 static and dynamic routing; VRRP; BFD; policy-based routing; GRE/6to4/ISATAP tunnels"),
    "ip_interface_capacity": t("256 IP interfaces"),
    "routing_entry_capacity": t("16K IPv4/IPv6 hardware routes; 32K shared L3 forwarding entries"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking": t("Physical ring/chain stacking; virtual stacking/cluster"),
    "stacking_bandwidth_gbps": n(80),
    "stacking_units": n(9),
    "operating_temperature_c": t("-5 to 50 °C"),
}


MODELS = {}
for suffix in ("", "/MI"):
    MODELS[f"DGS-3630-28TC{suffix}"] = {
        **COMMON,
        "ethernet_interfaces": t("20 x 10/100/1000BASE-T; 4 x GbE RJ45/SFP combo; 4 x 10GbE SFP+"),
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(95.24),
        "max_power_consumption_w": n(42.4),
        "dimensions_mm": t("441 x 259.8 x 44 mm"),
    }
    MODELS[f"DGS-3630-52TC{suffix}"] = {
        **COMMON,
        "ethernet_interfaces": t("44 x 10/100/1000BASE-T; 4 x GbE RJ45/SFP combo; 4 x 10GbE SFP+"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(130.95),
        "max_power_consumption_w": n(62),
        "dimensions_mm": t("441 x 259.8 x 44 mm"),
    }
    MODELS[f"DGS-3630-28PC{suffix}"] = {
        **COMMON,
        "fan_design": t("4 smart fans"),
        "ethernet_interfaces": t("20 x 10/100/1000BASE-T PoE; 4 x GbE PoE/SFP combo; 4 x 10GbE SFP+"),
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(95.24),
        "poe_configuration": t("24 PoE+ copper ports; 370 W internal / 740 W with DPS-700 RPS"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(469.3),
        "dimensions_mm": t("441 x 380 x 44 mm"),
    }
    MODELS[f"DGS-3630-52PC{suffix}"] = {
        **COMMON,
        "fan_design": t("4 smart fans"),
        "ethernet_interfaces": t("44 x 10/100/1000BASE-T PoE; 4 x GbE PoE/SFP combo; 4 x 10GbE SFP+"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(130.95),
        "poe_configuration": t("48 PoE+ copper ports; 370 W internal / 740 W with DPS-700 RPS"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(485),
        "dimensions_mm": t("441 x 380 x 44 mm"),
    }


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-3630 base and /MI specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")
        codes = {code for values in MODELS.values() for code in values} | POE_CODES
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version=SOURCE_VERSION,
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "D-Link DGS-3630 Series Layer 3 Stackable Managed Switches Datasheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        updated = not_applicable = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, data) in values.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from current official D-Link v8.04 WW datasheet; /MI is the MPLS software image on the same hardware.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(data)
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Technical specifications and software image tables - {model.replace('/MI', '')}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1
            if "PC" not in model:
                for code in POE_CODES:
                    definition = definitions[code]
                    spec, _ = ProductSpec.objects.update_or_create(
                        product=product,
                        definition=definition,
                        defaults={
                            "value_status": ProductSpec.ValueStatus.NOT_APPLICABLE,
                            "value_text": "",
                            "value_number": None,
                            "value_boolean": None,
                            "normalized_value": "",
                            "unit": definition.unit,
                            "raw_value": "Not a PoE model",
                            "source_url": SOURCE_URL[:200],
                            "source_note": "Official interface table identifies this as a non-PoE model.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=source,
                        source_location=f"Technical specifications - {model.replace('/MI', '')}",
                        defaults={
                            "source_excerpt": "Non-PoE interface configuration",
                            "evidence_level": SpecEvidence.EvidenceLevel.A,
                            "verified_at": timezone.now(),
                        },
                    )
                    not_applicable += 1
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} not_applicable={not_applicable} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
