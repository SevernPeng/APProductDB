from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


VALUES = {
    "ethernet_interfaces": ("5 x 10/100/1000 Mbps auto-sensing LAN ports", "5-10/100/1000 LAN ports"),
    "dimensions_mm": ("120 x 88 x 26 mm", "Version 2: 120 x 88 x 26 mm (W x D x H)"),
    "installation": ("Desktop", "Version 2 mountable: Desktop"),
    "operating_temperature_c": ("0°C to 40°C", "Version 2 operating temperature: 32 to 104°F (0 to 40°C)"),
    "qos_support": ("IEEE 802.1p", "Version 2 QoS: 802.1p"),
}


class Command(BaseCommand):
    help = "Import manually verified Linksys SE3005 v2 specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Linksys").first()
        product = Product.objects.filter(brand=brand, model="SE3005", is_published=True).first() if brand else None
        if not brand or not product:
            raise CommandError("Missing Linksys SE3005")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        url = "https://support.linksys.com/kb/article/3778-en/?section_id=189"
        version = "Official Linksys comparison including SE3005 v2; current copy accessed 2026-10-15"
        document, _ = SourceDocument.objects.update_or_create(
            url=url, document_version=version,
            defaults={
                "brand": brand, "product": product,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "Linksys SE3005 / SE3005 v2 Product Comparison",
                "region": "Worldwide", "published_date": None,
                "accessed_date": accessed, "active": True,
            },
        )

        new = corrected = unchanged = 0
        for code, (value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (old.value_text or "").strip())
            old_value = old.value_text if had else None
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value, "value_number": None, "value_boolean": None,
                    "normalized_value": value, "unit": definition.unit, "raw_value": raw,
                    "source_url": url[:200],
                    "source_note": "Manually verified from the official Linksys comparison; the newer SE3005 v2 values are used where versions differ.",
                    "verified_date": accessed,
                },
            )
            if not had:
                new += 1
            elif old_value != value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=document,
                source_location=f"SE3005 v2 comparison table - {code}",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.C,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(VALUES)} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models=1"
        ))
