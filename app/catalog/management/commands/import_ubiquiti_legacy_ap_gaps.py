from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://dl.ui.com/qsg/UAP-IW/UAP-IW_EN.html"
VALUES = {
    "poe_output": "48 V PoE passthrough on one 10/100 Ethernet port for an 802.3af device",
    "wireless_security": "WEP; WPA-PSK; WPA-Enterprise; WPA/WPA2; TKIP/AES",
}


class Command(BaseCommand):
    help = "Fill manually verified gaps for legacy Ubiquiti access points from official guides."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        product = Product.objects.filter(brand=brand, model="UAP-IW", is_published=True).first()
        if not brand or not product:
            raise CommandError("Published Ubiquiti UAP-IW was not found.")
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=VALUES)}
        if set(VALUES) - definitions.keys():
            raise CommandError("Required specification definitions were not found.")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Official UAP-IW Quick Start Guide (accessed 2026-10-12)",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "Ubiquiti UAP-IW Quick Start Guide",
                "region": "Global",
                "accessed_date": accessed,
                "active": True,
            },
        )
        for code, value in VALUES.items():
            definition = definitions[code]
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value,
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": value,
                    "unit": definition.unit,
                    "raw_value": value,
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the official legacy UAP-IW guide.",
                    "verified_date": accessed,
                },
            )
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Specifications and Hardware Overview",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {value}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={len(VALUES)} models=1"))
