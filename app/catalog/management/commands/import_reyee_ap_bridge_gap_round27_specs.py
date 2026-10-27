from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP2260(H)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap2260h/",
        "values": {"centralized_management": ("Ruijie Cloud", "Free cloud management; centralized network management; remote monitoring and maintenance")},
        "clear": {},
    },
    "RG-RAP52-OD": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-outdoor-ap/rap52od/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Cloud management; self-organizing network; cloud portal authentication"),
            "dimensions_mm": ("50 x 35.7 x 220 mm; antenna length 185 mm", "Product dimensions: 50 mm x 35.7 mm x 220 mm excluding bracket and antenna; antenna size: 185 mm"),
        },
        "clear": {},
    },
    "RG-RAP62": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap62/",
        "values": {"centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Standalone portal via Ruijie Cloud; official deployment workflow uses Ruijie Reyee App and Ruijie Cloud")},
        "clear": {},
    },
    "RG-RAP72Pro": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rg-rap72pro/",
        "values": {"centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Official deployment and configuration resources use Ruijie Reyee App and Ruijie Cloud")},
        "clear": {},
    },
    "RG-AirMetro460F": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/airmetro-series/rg-airmetro460f/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Available on both Ruijie Cloud and Ruijie Reyee App"),
            "max_channel_width_mhz": (80, "5 GHz channel width: Auto/20/40/80 MHz"),
        },
        "clear": {"wireless_security": "Existing value was broadcast-storm control, not a wireless-security specification."},
    },
    "RG-AirMetro460G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/airmetro-series/rg-airmetro460g/",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Available on both Ruijie Cloud and Ruijie Reyee App"),
            "max_channel_width_mhz": (80, "5 GHz channel width: Auto/20/40/80 MHz"),
        },
        "clear": {},
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    if spec.value_boolean is not None:
        return spec.value_boolean
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import/correct manually verified Reyee AP and bridge product-page specs (round 27)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in set(row["values"]) | set(row["clear"])}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        written = new = corrected = unchanged = cleared = 0
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
            model_new = model_corrected = model_cleared = 0
            for code, note in row["clear"].items():
                spec = ProductSpec.objects.filter(product=product, definition=definitions[code]).first()
                if actual(spec) is None:
                    continue
                spec.evidence.all().delete()
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""; spec.value_number = None; spec.value_boolean = None
                spec.normalized_value = ""; spec.raw_value = ""; spec.source_url = ""
                spec.source_note = f"Manual source audit: {note}"; spec.verified_date = accessed
                spec.save()
                cleared += 1; model_cleared += 1
            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
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
                              "source_note": "Manually verified from the current official Reyee product page.",
                              "verified_date": accessed},
                )
                if old_value is None:
                    new += 1; model_new += 1
                elif old_value != new_value:
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
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}/cleared:{model_cleared}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} cleared={cleared} models={len(PRODUCTS)}"))
        self.stdout.write("; ".join(details))
