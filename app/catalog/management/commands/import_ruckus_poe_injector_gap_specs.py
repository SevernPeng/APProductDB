from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/RUCKUS%2BAccessory%2BGuide/bbcc8a52d7ad11f0a98566254722ed67"
SOURCE_TITLE = "RUCKUS Accessory Guide"
SOURCE_VERSION = "Official 2026 edition; accessed 2026-10-21"


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("902-0162-XX00", "accessory_data_rate_gbps", "number", 1, "PoE module: 10/100/1000 Mbps", "Electrical accessories table"),
    i("902-0162-XX00", "accessory_input_power", "text", "100-240 VAC, 50/60 Hz", "AC input: 100-240 VAC, 50/60 Hz", "Electrical accessories table"),
    i("902-0162-XX00", "accessory_output_power", "text", "24 W PoE", "PoE port: RJ-45 jack, 24 Watts PoE", "Electrical accessories table"),
    i("902-0162-XX00", "accessory_poe_standard", "text", "PoE (24 W; IEEE class not stated)", "Regional PoE Adapter; PoE port provides 24 Watts PoE", "Electrical accessories table"),
    i("902-0162-XX00", "accessory_power_w", "number", 24, "PoE port: 24 Watts PoE", "Electrical accessories table"),
    i("902-0162-XX00", "accessory_compatibility", "text", "E510; H320; H350; H510; M510; P300; R310; R320; R350; R510; R550; R610; R710", "Compatible products: E510, H320, H350, H510, M510, P300, R310, R320, R350, R510, R550, R610, R710", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_data_rate_gbps", "number", 10, "PoE module: 10/100/1000/2500/5000/10000 Mbps", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_input_power", "text", "100-240 VAC, 50/60 Hz, 1.2 A", "Input: 100-240VAC, 50/60Hz, 1.2A", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_output_power", "text", "54 VDC, 1.12 A (60 W)", "Output: 54VDC 1.12A (60W)", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_poe_standard", "text", "PoE (up to 60 W; IEEE class not stated)", "Power-over-Ethernet adapter; supports power up to 60W", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_power_w", "number", 60, "Supports power up to 60W", "Electrical accessories table"),
    i("902-1180-XX00", "accessory_compatibility", "text", "R370; R560; R650; R670; R730; R750; R770; R850", "Compatible products: R370, R560, R650, R670, R730, R750, R770, R850", "Electrical accessories table"),
    i("902-1180-XX00", "dimensions_mm", "text", "123 x 61 x 40 mm", "Dimensions: 123 x 61 x 40 mm", "Electrical accessories table"),
]


class Command(BaseCommand):
    help = "Correct the RUCKUS 902-0162 SKU typo and import official PoE injector specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")

        product_0162 = Product.objects.filter(brand=brand, model="902-0162-XX00", is_published=True).first()
        if not product_0162:
            product_0162 = Product.objects.filter(brand=brand, model="902-1162-XX00", is_published=True).first()
            if not product_0162:
                raise CommandError("Missing RUCKUS product alias: 902-1162-XX00")
            canonical = product_0162.product_model
            canonical.model = "902-0162-XX00"
            canonical.save()
            product_0162.model = "902-0162-XX00"
            product_0162.notes = (product_0162.notes + "\nCorrected model typo from 902-1162-XX00 to official SKU 902-0162-XX00 using the 2026 RUCKUS Accessory Guide.").strip()
            product_0162.save()

        products = {
            "902-0162-XX00": product_0162,
            "902-1180-XX00": Product.objects.filter(brand=brand, model="902-1180-XX00", is_published=True).first(),
        }
        if not products["902-1180-XX00"]:
            raise CommandError("Missing RUCKUS product: 902-1180-XX00")

        codes = {x["code"] for x in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        document, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version=SOURCE_VERSION,
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": SOURCE_TITLE,
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        newly_filled = corrected = unchanged = 0
        for x in ITEMS:
            product = products[x["model"]]
            definition = definitions[x["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
            ))
            if x["kind"] == "number":
                old, new = (existing.value_number if had else None), Decimal(str(x["value"]))
            elif x["kind"] == "boolean":
                old, new = (existing.value_boolean if had else None), bool(x["value"])
            else:
                old, new = (existing.value_text if had else None), str(x["value"])
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(x["value"]),
                "unit": definition.unit,
                "raw_value": x["raw"],
                "source_url": SOURCE_URL[:200],
                "source_note": "Manually verified from the official 2026 RUCKUS Accessory Guide.",
                "verified_date": accessed,
            }
            if x["kind"] == "number":
                defaults["value_number"] = new
            elif x["kind"] == "boolean":
                defaults["value_boolean"] = new
            else:
                defaults["value_text"] = new
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old != new:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=document,
                source_location=x["location"],
                defaults={
                    "source_excerpt": x["raw"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: corrected_model=902-0162-XX00 spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
