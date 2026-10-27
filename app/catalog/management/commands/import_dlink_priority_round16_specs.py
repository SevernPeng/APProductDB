from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


class Command(BaseCommand):
    help = "Import manually verified D-Link DAP-2610 mesh support (round 16)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        product = Product.objects.filter(brand=brand, model="DAP-2610", is_published=True).first() if brand else None
        definition = SpecDefinition.objects.filter(code="mesh_support").first()
        if not brand or not product or not definition:
            raise CommandError("Missing D-Link, DAP-2610, or mesh_support definition")

        accessed = timezone.localdate()
        url = "https://www.dlink.com/de/de/press-centre/press-releases/2017/may/04/de_dap2610"
        version = "Official D-Link product release dated 2017-05-04; accessed 2026-10-15"
        document, _ = SourceDocument.objects.update_or_create(
            url=url, document_version=version,
            defaults={
                "brand": brand, "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "D-Link DAP-2610 Product Release", "region": "Germany",
                "published_date": None, "accessed_date": accessed, "active": True,
            },
        )

        old = ProductSpec.objects.filter(product=product, definition=definition).first()
        had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and old.value_boolean is not None)
        old_value = old.value_boolean if had else None
        spec, _ = ProductSpec.objects.update_or_create(
            product=product, definition=definition,
            defaults={
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": True,
                "normalized_value": "true", "unit": definition.unit,
                "raw_value": "Can be used as a mesh element; WDS enables mesh configurations",
                "source_url": url[:200],
                "source_note": "Manually verified from the cited official D-Link product release.",
                "verified_date": accessed,
            },
        )
        SpecEvidence.objects.update_or_create(
            product_spec=spec, source_document=document,
            source_location="Product description - DAP-2610",
            defaults={
                "source_excerpt": "DAP-2610 can be used as a mesh element; WDS enables mesh configurations.",
                "evidence_level": SpecEvidence.EvidenceLevel.B,
                "verified_at": timezone.now(),
            },
        )

        new = int(not had)
        corrected = int(had and old_value is not True)
        unchanged = int(had and old_value is True)
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values=1 newly_filled={new} corrected={corrected} unchanged={unchanged} models=1"
        ))
