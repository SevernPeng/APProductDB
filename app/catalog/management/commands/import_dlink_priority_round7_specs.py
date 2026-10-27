from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


DEM_300 = "https://support.dlink.com/resource/PRODUCTS/DEM-310GT/REVA/DEM-SERIES_DATASHEET_1.10_EN_US.pdf"
DEM_400 = "https://support.dlink.com/resource/PRODUCTS/DEM-400-Series/DEM-400%20Series_DATASHEET_v4.01_WW.pdf"
DEM_CABLES = "https://www.dlink.com/rs/sr/-/media/business_products/dem/dem-cbx00s/dem_cb100s_dem_cb300s_datasheet_en_eu.pdf"


PRODUCTS = {
    "DEM-310GT": {
        "url": DEM_300,
        "title": "D-Link DEM optical transceiver series datasheet v1.10",
        "location": "DEM-310GT (I1) technical-specification column",
        "shared": True,
        "values": {
            "accessory_compatibility": t("D-Link switches with SFP/mini-GBIC ports; IEEE 802.3z 1000BASE-LX"),
            "accessory_max_distance_km": n(10, "10 km over 9/125 μm single-mode fibre"),
            "operating_temperature_c": t("0 to 70 °C"),
        },
    },
    "DEM-410T": {
        "url": DEM_400,
        "title": "D-Link DEM-400 Series 10G transceiver datasheet v4.01",
        "location": "DEM-410T technical-specification column",
        "shared": True,
        "values": {
            "accessory_compatibility": t("SFP+ ports supporting IEEE 802.3an 10GBASE-T; RJ45 Cat 6a"),
            "accessory_max_distance_km": n(0.03, "30 m over Cat 6a"),
            "operating_temperature_c": t("0 to 60 °C"),
        },
    },
    "DEM-431XT": {
        "url": DEM_400,
        "title": "D-Link DEM-400 Series 10G transceiver datasheet v4.01",
        "location": "DEM-431XT technical-specification column",
        "shared": True,
        "values": {
            "accessory_compatibility": t("SFP+ ports supporting IEEE 802.3ae 10GBASE-SR; duplex LC multimode fibre"),
            "accessory_max_distance_km": n(0.3, "Up to 300 m over OM3/OM4 multimode fibre"),
            "operating_temperature_c": t("0 to 70 °C"),
        },
    },
    "DEM-432XT": {
        "url": DEM_400,
        "title": "D-Link DEM-400 Series 10G transceiver datasheet v4.01",
        "location": "DEM-432XT technical-specification column",
        "shared": True,
        "values": {
            "accessory_compatibility": t("SFP+ ports supporting IEEE 802.3ae 10GBASE-LR; duplex LC single-mode fibre"),
            "accessory_max_distance_km": n(10, "10 km over 9/125 μm single-mode fibre"),
        },
    },
    "DEM-CB100S": {
        "url": DEM_CABLES,
        "title": "D-Link DEM-CB100S/DEM-CB300S direct-attach cable datasheet",
        "location": "DEM-CB100S column and shared specifications, pp. 1-2",
        "shared": True,
        "values": {
            "accessory_fiber_mode": t("Not applicable — passive copper Twinax direct-attach cable"),
            "accessory_max_distance_km": n(0.001, "1 metre fixed cable length"),
            "operating_temperature_c": t("-40 to 85 °C"),
        },
    },
    "DEM-CB300S": {
        "url": DEM_CABLES,
        "title": "D-Link DEM-CB100S/DEM-CB300S direct-attach cable datasheet",
        "location": "DEM-CB300S column and shared specifications, pp. 1-2",
        "shared": True,
        "values": {
            "accessory_fiber_mode": t("Not applicable — passive copper Twinax direct-attach cable"),
            "accessory_max_distance_km": n(0.003, "3 metre fixed cable length"),
            "operating_temperature_c": t("-40 to 85 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link transceiver and direct-attach cable specifications (round 7)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
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
                raise CommandError(f"Missing published D-Link product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current official document accessed 2026-10-14",
                defaults={
                    "brand": brand,
                    "product": None if row.get("shared") else product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global/official regional support",
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
                    "source_note": "Manually verified from the exact model column in the official D-Link datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
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
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{row['location']} - {model}",
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
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
