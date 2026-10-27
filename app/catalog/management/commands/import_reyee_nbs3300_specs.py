from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


MODEL = "RG-NBS3300-8MG2XS-P"
URL = "https://reyee.ruijie.com/en-global/products/sme/switches/rg-nbs3300-8mg2xs-p/"
VALUES = {
    "ethernet_interfaces": t("8 x 10/100/1000/2500BASE-T PoE+ ports; 2 x 10GE SFP+ uplink ports"),
    "switching_capacity_gbps": n(80),
    "packet_forwarding_rate_mpps": n(59.52),
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("Ruijie Cloud remote management; Ruijie Reyee app; local management"),
    "poe_configuration": t("8 x PoE/PoE+ output ports; 240 W PoE budget"),
    "poe_standard": t("IEEE 802.3af/at"),
    "poe_ports": n(8),
    "poe_budget_w": n(240),
    "max_poe_per_port_w": n(30),
    "l2_features": t("Link aggregation; IGMP snooping; VLAN; PoE watchdog"),
    "acl_security": t("Multiple security policies; port isolation; broadcast storm control; CPU protection"),
    "operating_temperature_c": t("0 to 50 °C"),
}


class Command(BaseCommand):
    help = "Import manually verified Reyee NBS3300-8MG2XS-P specifications from its current official page."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Brand 'Reyee' was not found.")
        product = Product.objects.filter(brand=brand, model=MODEL, is_published=True).first()
        if not product:
            raise CommandError(f"Published model '{MODEL}' was not found.")
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=VALUES)}
        if VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(VALUES.keys() - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Current official product page (accessed 2026-09-23)",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": f"Reyee {MODEL} official product page",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        updated = 0
        for code, (kind, data) in VALUES.items():
            definition = definitions[code]
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(data),
                "unit": definition.unit,
                "raw_value": str(data),
                "source_url": URL[:200],
                "source_note": "Manually verified in a browser from the current official Reyee product page.",
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
                source_location="Highlights, key specifications, and software specifications",
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
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models=1"))
