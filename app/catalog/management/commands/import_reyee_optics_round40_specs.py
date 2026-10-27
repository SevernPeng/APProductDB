from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "GE-SFP-LX20-SM1310-BIDI": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/ge-sfp-lx20-sm1310-bidi",
        "compatibility": "SFP ports supporting 1000BASE-X; BIDI LC single-mode fiber",
    },
    "GE-SFP-LX20-SM1550-BIDI": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/ge-sfp-lx20-sm1550-bidi",
        "compatibility": "SFP ports supporting 1000BASE-X; BIDI LC single-mode fiber",
    },
    "MINI-GBIC-SX-MM850": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/mini-gbic-sx-mm850",
        "compatibility": "SFP ports supporting 1000BASE-X; duplex LC multimode fiber",
    },
    "Mini-GBIC-LX-SM1310": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/mini-gbic-lx-sm1310",
        "compatibility": "SFP ports supporting 1000BASE-X; duplex LC single-mode fiber",
    },
    "XG-SFP-LR-SM1310": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/xg-sfp-lr-sm1310",
        "compatibility": "SFP+ ports supporting 10GBASE-X; duplex LC single-mode fiber",
    },
    "XG-SFP-SR-MM850": {
        "url": "https://www.ruijie.com/en-global/products/switches/accessories/xg-sfp-sr-mm850",
        "compatibility": "SFP+ ports supporting 10GBASE-X; duplex LC multimode fiber",
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import manually verified Ruijie/Reyee optical-module dimensions and compatibility (round 40)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {d.code: d for d in SpecDefinition.objects.filter(
            code__in=["dimensions_mm", "accessory_compatibility"]
        )}
        if not brand or len(definitions) != 2:
            raise CommandError("Missing Reyee brand or accessory definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"], document_version="Current official optical-module specification table",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"{model} Official Product Page and Datasheet",
                    "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            values = {
                "dimensions_mm": ("56.5 x 13.5 x 8.5 mm (W x D x H)", "Dimensions (W x D x H): 56.5 mm x 13.5 mm x 8.5 mm"),
                "accessory_compatibility": (row["compatibility"], f"Form factor and media compatibility: {row['compatibility']}"),
            }
            model_new = model_corrected = 0
            for code, (value, raw) in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": value, "value_number": None, "value_boolean": None,
                        "normalized_value": value, "unit": definition.unit,
                        "raw_value": raw, "source_url": row["url"][:200],
                        "source_note": "Manually verified from the current official Ruijie product specification table.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1
                    model_new += 1
                elif old_value != value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location="Optical module specifications and order information tables",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
