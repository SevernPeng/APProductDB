from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, ProductType, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/RUCKUS%2BICX%2B8100%2BSwitch%2BData%2BSheet/4cfa1ca2d7a311f0a7d1fae0b00880c9"
SOURCE_VERSION = "PA-119962.4-EN (08/26)"


def n(value):
    return "number", value


def t(value):
    return "text", value


COMMON = {
    "mac_address_table": t("32,768 entries"),
    "packet_buffer_mb": n(4),
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("Web (HTTP/HTTPS); CLI; SSH; Telnet; SNMPv1/v2c/v3; sFlow; RUCKUS One; SmartZone; Unleashed"),
    "vlan_count": n(4095),
    "l2_features": t("MSTP; PVST/PVST+/RPVST; IGMP/MLD snooping; LACP; Q-in-Q; private VLAN; MVR; port/VLAN/ACL mirroring"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; PVST/PVST+/RPVST; BPDU Guard; Root Guard"),
    "acl_security": t("Port and Layer 3/4 ACLs; 802.1X; MAC/Web authentication; DHCP snooping; Dynamic ARP Inspection; Neighbor Discovery Inspection"),
    "operating_temperature_c": t("0 to 45 °C"),
    "stacking": t("Up to 4 switches; marked as a future software release in the August 2026 datasheet"),
}


MODEL_VALUES = {
    "ICX8100-24P": {
        "ethernet_interfaces": t("24 x GbE PoE+ RJ45; 4 x 1GbE SFP uplinks"),
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "power_supply": t("Integrated 550 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("24 x IEEE 802.3at Class 4 PoE+ ports; 370 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(435),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX8100-24P-X": {
        "ethernet_interfaces": t("24 x GbE PoE+ RJ45; 4 x 10GbE SFP+ uplinks"),
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "power_supply": t("Integrated 550 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("24 x IEEE 802.3at Class 4 PoE+ ports; 370 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(435),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX8100-48P": {
        "ethernet_interfaces": t("48 x GbE PoE+ RJ45; 4 x 1GbE SFP uplinks"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(132),
        "power_supply": t("Integrated 550 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("48 x IEEE 802.3at Class 4 PoE+ ports; 370 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(470),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX8100-48P-X": {
        "ethernet_interfaces": t("48 x GbE PoE+ RJ45; 4 x 10GbE SFP+ uplinks"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(132),
        "power_supply": t("Integrated 550 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("48 x IEEE 802.3at Class 4 PoE+ ports; 370 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(470),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX8100-48PF": {
        "ethernet_interfaces": t("48 x GbE PoE+ RJ45; 4 x 1GbE SFP uplinks"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(132),
        "power_supply": t("Integrated 920 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("48 x IEEE 802.3at Class 4 PoE+ ports; 740 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(848),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX8100-48PF-X": {
        "ethernet_interfaces": t("48 x GbE PoE+ RJ45; 4 x 10GbE SFP+ uplinks"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(132),
        "power_supply": t("Integrated 920 W AC power supply"),
        "fan_design": t("Front/side-to-back airflow; configurable fanless mode with PoE limited to 150 W"),
        "poe_configuration": t("48 x IEEE 802.3at Class 4 PoE+ ports; 740 W budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(848),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified RUCKUS ICX 8100 specs and correct the family to Layer 2 PoE."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Brand 'RUCKUS' was not found.")
        l2_poe = ProductType.objects.filter(category__slug="managed-switches", code="l2_poe").first()
        if not l2_poe:
            raise CommandError("Managed-switch product type 'l2_poe' was not found.")
        codes = set(COMMON) | {code for values in MODEL_VALUES.values() for code in values}
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
                "title": "RUCKUS ICX 8100 Enterprise-Class Access Switch Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        updated = reclassified = 0
        missing_models = []
        for model, model_values in MODEL_VALUES.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            if product.product_type_id != l2_poe.id:
                product.product_type = l2_poe
                product.save(update_fields=("product_type", "updated_at"))
                reclassified += 1
            values = {**COMMON, **model_values}
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
                    "source_note": "Manually verified from the August 2026 official RUCKUS data sheet; -X denotes 10GbE rather than 1GbE uplinks.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Feature/model comparison, specifications, and ordering information - {model}",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={updated} reclassified={reclassified} models={len(MODEL_VALUES) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
