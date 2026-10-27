from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


COMMON = {
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("Ruijie Cloud web portal and mobile app; local eWeb management"),
    "vlan_count": n(4094),
    "l2_features": t("Link aggregation; IGMP snooping v1/v2; VLAN; voice VLAN; LLDP/LLDP-MED; port isolation; broadcast storm control"),
    "stp_features": t("STP and RSTP"),
    "acl_security": t("ACL; port isolation; broadcast storm control; multiple security policies"),
    "operating_temperature_c": t("0 to 50 °C"),
}


MODELS = {
    "RG-NBS3200-24GT4XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-24gt4xs/",
        "values": {
            "ethernet_interfaces": t("24 x 10/100/1000Base-T; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.23),
        },
    },
    "RG-NBS3200-24GT4XS-P": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-24gt4xs-p/",
        "values": {
            "ethernet_interfaces": t("24 x 10/100/1000Base-T PoE+; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.23),
            "poe_configuration": t("24 x PoE/PoE+ ports; 370 W PoE budget"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(24),
            "poe_budget_w": n(370),
            "max_poe_per_port_w": n(30),
        },
    },
    "RG-NBS3200-24SFP/8GT4XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-24sfp-8gt4xs/",
        "values": {
            "ethernet_interfaces": t("24 x 1GbE SFP including 8 combo GbE RJ45 ports; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.23),
        },
    },
    "RG-NBS3200-48GT4XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-48gt4xs/",
        "values": {
            "ethernet_interfaces": t("48 x 10/100/1000Base-T; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(176),
            "packet_forwarding_rate_mpps": n(131),
        },
    },
    "RG-NBS3200-48GT4XS-P": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-48gt4xs-p/",
        "values": {
            "ethernet_interfaces": t("48 x 10/100/1000Base-T PoE+; 4 x 10GbE SFP+ uplinks"),
            "switching_capacity_gbps": n(176),
            "packet_forwarding_rate_mpps": n(132),
            "poe_configuration": t("48 x PoE/PoE+ ports; 370 W PoE budget"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(48),
            "poe_budget_w": n(370),
            "max_poe_per_port_w": n(30),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee NBS3200 specifications from current official product pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Brand 'Reyee' was not found.")
        codes = set(COMMON) | {code for item in MODELS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        updated = 0
        missing_models = []
        for model, item in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official product page (accessed 2026-09-23)",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Reyee {model} official product page",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            for code, (kind, data) in {**COMMON, **item["values"]}.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from the current official Reyee product page and comparison table.",
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
                    source_location=f"Highlights, comparison, key specifications, and software specifications - {model}",
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
            f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
