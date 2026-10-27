from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP2200(E)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap2200e/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Cloud App", "Free cloud management; centralized management; setup through Ruijie Cloud App"),
            "dimensions_mm": ("194 x 194 x 35 mm", "Product dimensions (W x D x H): 194 mm x 194 mm x 35 mm, excluding mounting bracket"),
            "ethernet_interfaces": ("2 x 10/100/1000BASE-T", "Number of 10/100/1000BASE-T ports: 2"),
        },
    },
    "RG-RAP2200(F)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap2200f/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Cloud App", "Free cloud management; centralized management; setup through Ruijie Cloud App"),
        },
    },
    "RG-RAP2260": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap2260/",
        "values": {
            "centralized_management": ("Ruijie Cloud", "Free cloud management; centralized network management; remote monitoring and maintenance"),
        },
    },
    "RG-RAP2260(G)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap2260g/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Cloud App", "Free cloud management; centralized management; setup through Ruijie Cloud App"),
            "dimensions_mm": ("194 x 194 x 35 mm", "Product dimensions (W x D x H): 194 mm x 194 mm x 35 mm, excluding mounting bracket"),
            "ethernet_interfaces": ("2 x 10/100/1000BASE-T", "Number of 10/100/1000BASE-T ports: 2"),
        },
    },
}


class Command(BaseCommand):
    help = "Import/correct manually verified Reyee indoor AP product-page specs (round 26)."

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
                url=row["url"], document_version="Current official product page, accessed 2026-10-21",
                defaults={"brand": brand, "product": product,
                          "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                          "title": f"{model} official product page", "region": "Global",
                          "published_date": None, "accessed_date": accessed, "active": True},
            )
            model_new = model_corrected = 0
            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = old.value_text if old and old.value_status == ProductSpec.ValueStatus.PUBLISHED else None
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={"value_status": ProductSpec.ValueStatus.PUBLISHED,
                              "value_text": value, "value_number": None, "value_boolean": None,
                              "normalized_value": value, "unit": definition.unit, "raw_value": raw,
                              "source_url": row["url"][:200],
                              "source_note": "Manually verified from the current official Reyee product page.",
                              "verified_date": accessed},
                )
                if not old_value:
                    new += 1; model_new += 1
                elif old_value != value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location="Features / Key Specifications",
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
