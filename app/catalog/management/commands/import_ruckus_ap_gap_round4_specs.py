from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "R510": ("https://webresources.ruckuswireless.com/datasheets/r510/ds-ruckus-r510.pdf", "RUCKUS R510 Data Sheet", "Official CommScope/RUCKUS 2020 data sheet; accessed 2026-10-21"),
    "R610": ("https://webresources.ruckuswireless.com/datasheets/r610/ds-ruckus-r610.pdf", "RUCKUS R610 Data Sheet", "Official CommScope/RUCKUS 2020 data sheet; accessed 2026-10-21"),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("R510", "power_method", "text", "IEEE 802.3af PoE; 12 VDC", "Power supply: 802.3af PoE or 12 VDC input", "Power"),
    i("R510", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    i("R510", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("R510", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R510", "max_power_consumption_w", "number", 12.6, "802.3af maximum power consumption: 12.6 W", "Power"),
    i("R510", "dimensions_mm", "text", "168 x 165 x 41 mm", "Physical Size: 16.8 x 16.5 x 4.1 cm", "Physical Characteristics"),
    i("R510", "operating_temperature_c", "text", "0 to 50 °C", "Operating Temperature: 0°C to 50°C", "Physical Characteristics"),

    i("R610", "power_method", "text", "IEEE 802.3af/at PoE; 12 VDC", "Power supply: 802.3af/at PoE or 12 VDC input", "Power"),
    i("R610", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    i("R610", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("R610", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R610", "max_power_consumption_w", "number", 21.87, "802.3at full-function maximum power consumption: 21.87 W", "Power"),
    i("R610", "dimensions_mm", "text", "201 x 195 x 51 mm", "Physical Size: 20.1 x 19.5 x 5.1 cm", "Physical Characteristics"),
    i("R610", "operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS R510/R610 access-point gap specifications."

    def add_arguments(self, parser): parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand: raise CommandError("Missing brand: RUCKUS")
        codes = {x["code"] for x in ITEMS}; definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys(): raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate(); docs = {}; newly_filled = corrected = unchanged = 0
        for x in ITEMS:
            url, title, version = SOURCES[x["model"]]
            if x["model"] not in docs:
                docs[x["model"]], _ = SourceDocument.objects.update_or_create(
                    url=url, document_version=version,
                    defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                              "title": title, "region": "Global", "published_date": None,
                              "accessed_date": accessed, "active": True})
            product = Product.objects.filter(brand=brand, model=x["model"], is_published=True).first()
            if not product: raise CommandError(f"Missing RUCKUS product: {x['model']}")
            definition = definitions[x["code"]]; existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None))
            if x["kind"] == "number": old, new = (existing.value_number if had else None), Decimal(str(x["value"]))
            elif x["kind"] == "boolean": old, new = (existing.value_boolean if had else None), bool(x["value"])
            else: old, new = (existing.value_text if had else None), str(x["value"])
            defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                        "value_boolean": None, "normalized_value": str(x["value"]), "unit": definition.unit,
                        "raw_value": x["raw"], "source_url": url[:200],
                        "source_note": "Manually verified from the official CommScope/RUCKUS model data sheet.",
                        "verified_date": accessed}
            if x["kind"] == "number": defaults["value_number"] = new
            elif x["kind"] == "boolean": defaults["value_boolean"] = new
            else: defaults["value_text"] = new
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had: newly_filled += 1
            elif old != new: corrected += 1
            else: unchanged += 1
            SpecEvidence.objects.update_or_create(product_spec=spec, source_document=docs[x["model"]], source_location=x["location"],
                defaults={"source_excerpt": x["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()})
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"))
