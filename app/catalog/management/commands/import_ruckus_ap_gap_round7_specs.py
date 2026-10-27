from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "R670": (
        "https://webresources.commscope.com/download/assets/Data%2BSheet:%2BR670/99acc26e3bd811f09165faa31792deb3",
        "RUCKUS R670 Data Sheet",
        "PA-118845.2-EN (10/25); accessed 2026-10-21",
    ),
    "R770": (
        "https://webresources.commscope.com/download/assets/DS-RUCKUS-R770-PA-118269-EN/046f4ad63bd411f09d0e068e18034550",
        "RUCKUS R770 Data Sheet",
        "PA-118269.3-EN (10/25); accessed 2026-10-21",
    ),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("R670", "max_power_consumption_w", "number", 35, "Power Consumption: DC Power 35W; 802.3bt/PoH/uPoE 35W", "Power Consumption"),
    i("R670", "centralized_management", "text", "SmartZone; RUCKUS Unleashed; RUCKUS One", "Controller Platform Support: SmartZone, RUCKUS Unleashed, RUCKUS One", "Networking"),
    i("R670", "mesh_support", "boolean", True, "Mesh: SmartMesh wireless meshing technology; self-healing mesh in 2.4, 5 and 6 GHz", "Networking"),
    i("R670", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R670", "operating_temperature_c", "text", "0 to 50 °C", "Operating Temperature: 0ºC (32ºF) to 50ºC (122ºF)", "Physical Characteristics"),
    i("R770", "max_power_consumption_w", "number", 40, "802.3bt/PoH/uPoE: 32W average/RMS, 40W peak/LLDP", "Power Consumption"),
    i("R770", "centralized_management", "text", "SmartZone; RUCKUS Unleashed; RUCKUS One", "Controller Platform Support: SmartZone, RUCKUS Unleashed, RUCKUS One", "Networking"),
    i("R770", "mesh_support", "boolean", True, "Mesh: SmartMesh wireless meshing technology; self-healing mesh in 2.4, 5 and 6 GHz", "Networking"),
    i("R770", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R770", "operating_temperature_c", "text", "-10 to 50 °C", "Operating Temperature: -10ºC (14ºF) to 50ºC (122ºF)", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified late-gap RUCKUS R670 and R770 specifications from the latest official data sheets."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        codes = {x["code"] for x in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        docs = {}
        newly_filled = corrected = unchanged = 0
        for x in ITEMS:
            url, title, version = SOURCES[x["model"]]
            if x["model"] not in docs:
                product = Product.objects.filter(brand=brand, model=x["model"], is_published=True).first()
                if not product:
                    raise CommandError(f"Missing RUCKUS product: {x['model']}")
                docs[x["model"]], _ = SourceDocument.objects.update_or_create(
                    url=url,
                    document_version=version,
                    defaults={
                        "brand": brand,
                        "product": product,
                        "document_type": SourceDocument.DocumentType.DATASHEET,
                        "title": title,
                        "region": "Global",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
            product = Product.objects.get(brand=brand, model=x["model"], is_published=True)
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
                "source_url": url[:200],
                "source_note": "Manually verified from the latest official CommScope/RUCKUS model data sheet.",
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
                source_document=docs[x["model"]],
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
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
