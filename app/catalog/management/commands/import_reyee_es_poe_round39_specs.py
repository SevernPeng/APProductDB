from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-ES206GC-P": "https://reyee-uat.ruijie.com/en-global/resources/preview/rg-es206gc-p-datasheet/",
    "RG-ES206GS-P": "https://eo-sgp-cos.ruijie.com/Document/pdf/2025/10/24/RG-ES206GS-P_Datasheet_Official_2025-10-24.pdf",
    "RG-ES206MG-P": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/rg-es206mg-p/",
    "RG-ES209GC-P": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/es209gc-p/",
    "RG-ES209MG-P": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/rg-es209mg-p/",
    "RG-ES210GS-P": "https://reyee.ruijie.com/en-global/resources/preview/rg-es210gs-p-datasheet/",
    "RG-ES220GS-P": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/rg-es220gs-p-v2/",
    "RG-ES228GS-LP": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/rg-es228gs-lp/",
    "RG-ES228GS-P": "https://reyee.ruijie.com/en-global/products/reyee-switch/smart-cctv-switch/es228gsp/",
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
    help = "Import manually verified Reyee ES-series maximum PoE-per-port specs (round 39)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definition = SpecDefinition.objects.filter(code="max_poe_per_port_w").first()
        if not brand or not definition:
            raise CommandError("Missing Reyee brand or max_poe_per_port_w definition")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, url in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=url, document_version="Newest available exact-model official product page/datasheet",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"{model} Official Product Page and Datasheet",
                    "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            new_value = Decimal("30")
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": new_value, "value_boolean": None,
                    "normalized_value": "30", "unit": definition.unit,
                    "raw_value": "PoE+ ports; IEEE 802.3at; maximum output power per port: 30 W",
                    "source_url": url[:200],
                    "source_note": "Manually verified from the newest available official exact-model product page and datasheet.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                outcome = "+1"
            elif old_value != new_value:
                corrected += 1
                outcome = "corrected:1"
            else:
                unchanged += 1
                outcome = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=source,
                source_location="Port specifications / PoE standards and per-port output table",
                defaults={
                    "source_excerpt": "Maximum PoE output per port: 30 W (PoE+, IEEE 802.3at)",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{model}:{outcome}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
