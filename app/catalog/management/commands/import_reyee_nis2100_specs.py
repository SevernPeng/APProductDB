from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


MODELS = {
    "RG-NIS2100-4GT2SFP-HP": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/industrial-switch/rg-nis2100-4gt2sfp-hp/",
        "values": {
            "ethernet_interfaces": t("4 x 10/100/1000BASE-T PoE ports; 2 x 1GE SFP uplink ports"),
            "packet_forwarding_rate_mpps": n(8.9),
            "switching_capacity_gbps": n(12),
            "power_supply": t("External power adapter required; adapter is not included"),
            "management_methods": t("Ruijie Cloud remote management; local management"),
            "poe_configuration": t("4 PoE output ports: port 1 supports PoE++; ports 2-4 support PoE+; default 108 W, adjustable maximum 180 W budget"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(4),
            "poe_budget_w": n(180),
            "max_poe_per_port_w": n(90),
            "l2_features": t("ERPS rapid failover; port isolation; PoE watchdog; LAN self-organizing network"),
            "acl_security": t("Port isolation"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
    "RG-NIS2100-8GT2SFP-HP": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/industrial-switch/rg-nis2100-8gt2sfp-hp/",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T PoE ports; 2 x 1GE SFP uplink ports"),
            "packet_forwarding_rate_mpps": n(14.8),
            "switching_capacity_gbps": n(20),
            "power_supply": t("External power adapter required; adapter is not included"),
            "management_methods": t("Ruijie Cloud remote management; local management"),
            "poe_configuration": t("8 PoE output ports: port 1 supports PoE++; ports 2-8 support PoE+; default 228 W, adjustable maximum 300 W budget"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(8),
            "poe_budget_w": n(300),
            "max_poe_per_port_w": n(90),
            "l2_features": t("ERPS rapid failover; port isolation; PoE watchdog; LAN self-organizing network"),
            "acl_security": t("Port isolation"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee NIS2100 specifications from current official product pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Brand 'Reyee' was not found.")
        codes = {code for item in MODELS.values() for code in item["values"]}
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
            for code, (kind, data) in item["values"].items():
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
                    "source_note": "Manually verified from the current official Reyee product page.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Highlights and key specifications - {model}",
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
