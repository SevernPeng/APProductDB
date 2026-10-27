from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


SOURCES = {
    "des1024d": {
        "url": "https://www.dlink.ru/en/products/1/2730.html",
        "version": "DES-1024D/H2/H2A official product page; accessed 2026-10-15",
        "title": "D-Link DES-1024D 24-Port Fast Ethernet Unmanaged Switch",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "evidence": SpecEvidence.EvidenceLevel.B,
    },
    "dss100e18p": {
        "url": "https://www.dlink.com/en/-/media/product-pages/dss/dss-100e-18p/assets/dss100eseriesa1datasheetv100ww.pdf",
        "version": "DSS-100E Series A1 datasheet v1.00 WW; accessed 2026-10-15",
        "title": "D-Link DSS-100E Series Unmanaged PoE Surveillance Switches Datasheet",
        "type": SourceDocument.DocumentType.DATASHEET,
        "evidence": SpecEvidence.EvidenceLevel.A,
    },
}


PRODUCTS = {
    "DES-1024D": {
        "packet_buffer_mb": (n(0.25, "256 Kbytes = 0.25 MB"), "des1024d", "Specifications, Switching specifications"),
        "jumbo_frame_bytes": (n(2048, "2 Kbytes = 2,048 bytes"), "des1024d", "Specifications, Switching specifications"),
    },
    "DSS-100E-18P": {
        "packet_buffer_mb": (n(0.344, "2.75 Mbits = 0.34375 MB; stored as 0.344 MB"), "dss100e18p", "Product comparison table"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link unmanaged-switch specifications (round 13)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, data in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=data["url"], document_version=data["version"],
                defaults={
                    "brand": brand, "product": None, "document_type": data["type"],
                    "title": data["title"], "region": "Worldwide", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )

        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, ((kind, value, raw), source_key, location) in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                source = SOURCES[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": source["url"][:200],
                    "source_note": "Manually verified from the cited official D-Link source; unit conversion is recorded in raw_value.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    raise CommandError(f"Unexpected value kind: {kind}")
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[source_key],
                    source_location=f"{location} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": source["evidence"],
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
