from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP2200(F)": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_ruijie-reyee-rg-rap2200-f-access-point-hardware-installation-and-reference-guide-en/",
        "version": "Installation Guide V1.5, 2025-10-17",
        "values": {
            "antenna_gain_dbi": ("2.4 GHz: 2 dBi; 5 GHz: 2 dBi", "Antenna gain: 2.00 dBi at 2.4 GHz and 2.00 dBi at 5 GHz"),
            "max_channel_width_mhz": (80, "5 GHz channel width: Auto/20/40/80 MHz"),
        },
    },
    "RG-RAP2260(H)": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_ruijie-reyee-rg-rap2260-h-access-point-hardware-installation-and-reference-guide-en/",
        "version": "Installation Guide V1.5, 2025-10-17",
        "values": {
            "antenna_gain_dbi": ("2.4 GHz: 3 dBi; 5 GHz: 4 dBi", "Antenna gain: 3.00 dBi at 2.4 GHz and 4.00 dBi at 5 GHz"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee AP installation-guide specs (round 28)."

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
                url=row["url"], document_version=row["version"],
                defaults={"brand": brand, "product": product,
                          "document_type": SourceDocument.DocumentType.SUPPORT,
                          "title": f"{model} official installation guide", "region": "Global",
                          "published_date": None, "accessed_date": accessed, "active": True},
            )
            model_new = model_corrected = 0
            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                if old and old.value_status == ProductSpec.ValueStatus.PUBLISHED:
                    old_value = old.value_number if old.value_number is not None else old.value_text
                else:
                    old_value = None
                is_number = isinstance(value, (int, float))
                new_value = Decimal(str(value)) if is_number else str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={"value_status": ProductSpec.ValueStatus.PUBLISHED,
                              "value_text": "" if is_number else str(value),
                              "value_number": new_value if is_number else None,
                              "value_boolean": None, "normalized_value": str(value),
                              "unit": definition.unit, "raw_value": raw,
                              "source_url": row["url"][:200],
                              "source_note": "Manually verified from the latest official Reyee installation guide.",
                              "verified_date": accessed},
                )
                if old_value in (None, ""):
                    new += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location="Technical Specifications",
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
