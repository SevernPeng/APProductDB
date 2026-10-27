from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE = {
    "url": "https://www.dlink.com/es/es/-/media/files/es/catalogos/dlinkcatalogoesonlineweb.pdf",
    "version": "Current official D-Link business Wi-Fi catalog; published 2026; accessed 2026-10-15",
    "title": "D-Link Business Wi-Fi Catalog",
}


PRODUCTS = {
    "DAP-E3620OU": "Fast Roaming",
    "DAP-E9560": "Fast Roaming",
    "DAP-X3060W": "Fast Roaming",
}


class Command(BaseCommand):
    help = "Import manually verified D-Link wireless AP fast-roaming specifications (round 15)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        definition = SpecDefinition.objects.filter(code="fast_roaming").first()
        if not definition:
            raise CommandError("Missing definition: fast_roaming")

        accessed = timezone.localdate()
        document, _ = SourceDocument.objects.update_or_create(
            url=SOURCE["url"], document_version=SOURCE["version"],
            defaults={
                "brand": brand, "product": None,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": SOURCE["title"], "region": "Europe", "published_date": None,
                "accessed_date": accessed, "active": True,
            },
        )

        written = new = corrected = unchanged = 0
        details = []
        for model, raw in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (old.value_text or "").strip())
            old_value = old.value_text if had else None
            value = "Supported"
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value, "value_number": None, "value_boolean": None,
                    "normalized_value": value, "unit": definition.unit, "raw_value": raw,
                    "source_url": SOURCE["url"][:200],
                    "source_note": "Manually verified from the cited official D-Link 2026 business Wi-Fi catalog.",
                    "verified_date": accessed,
                },
            )
            if not had:
                new += 1
                detail = "+1"
            elif old_value != value:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged"
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=document,
                source_location=f"p. 21, access point comparison - {model}",
                defaults={
                    "source_excerpt": f"{model}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.C,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{model}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
