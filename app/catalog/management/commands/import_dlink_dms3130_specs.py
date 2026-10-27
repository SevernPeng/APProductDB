from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.dlink.com/en/-/media/business_products/dms/dms-3130/datasheet/dms3130seriesa1datasheetv101ww.pdf"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "jumbo_frame_bytes": n(12288),
    "vlan_count": n(4094),
    "l2_features": t(
        "802.1Q; GVRP; QinQ; private, voice, MAC-, protocol- and port-based VLANs; "
        "802.1AX/802.3ad link aggregation; ERPS v1/v2; IGMP/MLD snooping; port/RSPAN/flow mirroring"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU filtering; root guard; loop guard"
    ),
    "acl_security": t(
        "Multi-layer and packet-content ACLs; 802.1X/Web/MAC authentication; DHCP snooping; "
        "IP source guard; DAI; IPv6 guards/inspection; DoS prevention; RADIUS/TACACS+"
    ),
    "ip_interface_capacity": t("128 IP interfaces"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "stacking": t("Physical stacking in ring or chain topology; up to 9 units"),
    "stacking_bandwidth_gbps": n(200),
}


MODELS = {
    "DMS-3130-30TS": {
        **COMMON,
    },
    "DMS-3130-30PS": {
        **COMMON,
        "management_methods": t(
            "Web GUI/HTTPS; CLI; out-of-band RJ45 console and management ports; Telnet; "
            "SNMP v1/v2c/v3; RMON v1/v2; sFlow; TFTP/SFTP; syslog; LLDP/LLDP-MED"
        ),
        "poe_standard": t("IEEE 802.3af/802.3at/802.3bt PoE/PoE+/PoE++"),
        "poe_ports": n(24),
        "poe_budget_w": n(960),
        "max_poe_per_port_w": n(60),
        "max_power_consumption_w": n(1211.5),
        "dimensions_mm": t("440 x 470 x 44 mm"),
        "operating_temperature_c": t("0 to 50 °C"),
    },
}


LOCATIONS = {
    "jumbo_frame_bytes": "Software features, p. 4",
    "management_methods": "Management features, p. 6",
    "poe_standard": "PoE support and technical specifications, pp. 2-3",
    "poe_ports": "Technical specifications, p. 3",
    "poe_budget_w": "PoE support and technical specifications, pp. 2-3",
    "max_poe_per_port_w": "PoE support, p. 2",
    "vlan_count": "Software features, p. 4",
    "l2_features": "Software features, p. 4",
    "stp_features": "Software features, pp. 1 and 4",
    "acl_security": "Security and ACL features, pp. 2 and 5-6",
    "ip_interface_capacity": "Layer 3 features, p. 6",
    "ospf_support": "Layer 3 routing, p. 7",
    "rip_support": "Layer 3 routing, p. 7",
    "pbr_support": "Layer 3 routing, p. 7",
    "stacking": "High-bandwidth stacking, pp. 1-2 and 4",
    "stacking_bandwidth_gbps": "High-bandwidth stacking, pp. 1 and 4",
    "max_power_consumption_w": "Physical specifications, p. 3",
    "dimensions_mm": "Physical specifications, p. 3",
    "operating_temperature_c": "Physical specifications, p. 3",
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DMS-3130 series specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")

        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Version 1.01 WW, updated 2023-11-02",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "D-Link DMS-3130 Series Layer 3 Stackable Managed Switches",
                "region": "Worldwide",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, value) in values.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": "12 Kbytes" if code == "jumbo_frame_bytes" else str(value),
                    "source_url": SOURCE_URL,
                    "source_note": (
                        "Manually verified from the official DMS-3130 series datasheet. "
                        "The PoE budget records the documented maximum with dual power supplies."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{LOCATIONS[code]} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {defaults['raw_value']}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
