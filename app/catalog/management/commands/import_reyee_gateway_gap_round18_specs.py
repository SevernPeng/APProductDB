from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-EG209GS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg209gs/",
        "values": {"concurrent_sessions": (200, "200 recommended concurrent clients")},
    },
    "RG-EG406XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg406xs/",
        "values": {
            "concurrent_sessions": (400, "400 recommended concurrent clients"),
            "ethernet_interfaces": ("5 x 10/100/1000/2500BASE-T RJ45 + 1 x 10GE SFP+", "5 x 2.5GbE RJ45 + 1 x 10GE SFP+"),
        },
    },
    "RG-EG710XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg710xs/",
        "values": {"concurrent_sessions": (700, "700 recommended concurrent clients")},
    },
    "RG-EG1510XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/eg1510xs/",
        "values": {"concurrent_sessions": (1500, "1500 recommended concurrent clients")},
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee gateway product-page specifications (round 18)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"], document_version="Current official global product page, accessed 2026-10-21",
                defaults={"brand": brand, "product": product,
                          "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                          "title": f"{model} official product page", "region": "Global",
                          "published_date": None, "accessed_date": accessed, "active": True},
            )
            model_new = model_corrected = 0
            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None))
                old_value = None if not had else old.value_text if old.value_text else old.value_number
                is_number = isinstance(value, (int, float))
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "",
                            "value_number": Decimal(str(value)) if is_number else None, "value_boolean": None,
                            "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                            "source_url": row["url"][:200],
                            "source_note": "Manually verified from the current official Reyee product page.",
                            "verified_date": accessed}
                if not is_number:
                    defaults["value_text"] = str(value)
                new_value = Decimal(str(value)) if is_number else str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    new += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"Key Specifications / System Performance Capacity - {model}",
                    defaults={"source_excerpt": f"{definition.display_name}: {raw}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A,
                              "verified_at": timezone.now()},
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"))
        self.stdout.write("; ".join(details))
