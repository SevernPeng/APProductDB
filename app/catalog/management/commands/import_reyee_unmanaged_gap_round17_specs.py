from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


PRODUCTS = {
    "RG-ES106D-P": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/20/RG-ES106D-P%20V2%20Switch%20Datasheet.pdf",
        "title": "RG-ES106D-P V2 Switch Datasheet",
        "values": {
            "ethernet_interfaces": t("6 x 10/100BASE-T RJ45"),
            "dimensions_mm": t("140 x 67 x 26 mm (W x D x H)"),
            "flow_control": t("DIP-switch selectable Flow Control On/Off"),
            "installation": t("Wall or desktop"),
            "fanless": b(True, "Fanless design"),
            "max_power_consumption_w": n(60.6, "60.6 W with full PoE load"),
        },
    },
    "RG-ES110D-P": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13/RG-ES110D-P_Datasheet_Official_2026-05-13.pdf",
        "title": "RG-ES110D-P Datasheet Official",
        "values": {
            "ethernet_interfaces": t("8 x 10/100BASE-T RJ45 + 2 x 10/100/1000BASE-T RJ45"),
            "dimensions_mm": t("190 x 100 x 28 mm (W x D x H)"),
            "flow_control": t("DIP-switch selectable Flow Control On/Off"),
            "installation": t("Wall or desktop"),
            "max_power_consumption_w": n(129, "129 W with full PoE load"),
        },
    },
    "RG-ES110GDS-P": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13/RG-ES110GDS-P_Datasheet_Official_2026-05-13.pdf",
        "title": "RG-ES110GDS-P Datasheet Official",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T RJ45 + 2 x 1GE SFP"),
            "dimensions_mm": t("280 x 180 x 44 mm (W x D x H)"),
            "flow_control": t("DIP-switch selectable Flow Control On/Off"),
            "installation": t("Wall or desktop"),
            "max_power_consumption_w": n(142, "142 W with full PoE load"),
        },
    },
    "RG-ES118GS-P": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13/RG-ES118GS-P_Datasheet_Official_2026-05-13.pdf",
        "title": "RG-ES118GS-P Datasheet Official",
        "values": {
            "ethernet_interfaces": t("16 x 10/100/1000BASE-T RJ45 + 2 x 1GE SFP"),
            "dimensions_mm": t("440 x 240 x 44 mm (W x D x H)"),
            "flow_control": t("DIP-switch selectable Flow Control On/Off"),
            "installation": t("Rack mount"),
            "fanless": b(False, "2 fixed fans"),
            "max_power_consumption_w": n(297, "297 W with full PoE load"),
        },
    },
    "RG-ES118S-LP": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/5/13/RG-ES118S-LP_Datasheet_Official_2026-05-13.pdf",
        "title": "RG-ES118S-LP Datasheet Official",
        "values": {
            "ethernet_interfaces": t("16 x 10/100BASE-T RJ45 + 2 x 10/100/1000BASE-T RJ45; 2 x 1GE SFP combo ports"),
            "dimensions_mm": t("440 x 208 x 44 mm (W x D x H)"),
            "flow_control": t("DIP-switch selectable Flow Control On/Off"),
            "installation": t("Rack mount"),
            "max_power_consumption_w": n(148, "148 W with full PoE load"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee unmanaged-switch datasheet specifications (round 17)."

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
                url=row["url"],
                document_version="Official datasheet dated 2026-05-12/13",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
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
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": (
                        "Manually verified from the latest official Reyee datasheet; maximum power uses the "
                        "datasheet's full-PoE-load value rather than its no-load value."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Hardware Specifications table - {model}",
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
