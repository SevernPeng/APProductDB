from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "T350": ("https://webresources.commscope.com/download/assets/RUCKUS%2BT350%2BData%2BSheet/f6e7d1ea3bd711f097831adcaa92e24e", "RUCKUS T350 Data Sheet", "PA-115633.4-EN (11/25); accessed 2026-10-21"),
    "T350se": ("https://webresources.commscope.com/download/assets/RUCKUS%2BT350%2BData%2BSheet/f6e7d1ea3bd711f097831adcaa92e24e", "RUCKUS T350 Data Sheet", "PA-115633.4-EN (11/25); accessed 2026-10-21"),
    "T670": ("https://www.commscope.com/globalassets/digizuite/997955-ruckus-T670-data-sheet-PA-118919-EN.pdf", "RUCKUS T670 Data Sheet", "PA-118919-EN (2024); accessed 2026-10-21"),
    "R350": ("https://webresources.commscope.com/download/assets/RUCKUS%2BR350%2BData%2BSheet/ccf181263bd511f099f1068e18034550", "RUCKUS R350 Data Sheet", "Official 2025 edition; accessed 2026-10-21"),
    "R550": ("https://webresources.commscope.com/download/assets/RUCKUS%2BR550%2BData%2BSheet/4378f5643bd511f0a4acea1fa90d937b", "RUCKUS R550 Data Sheet", "Official 2025 edition; accessed 2026-10-21"),
    "H350": ("https://webresources.vistancenetworks.com/download/assets/RUCKUS%2BH350%2BData%2BSheet/caa097a8d7a311f0a98566254722ed67", "RUCKUS H350 Data Sheet", "PA-116171.2-EN (12/25); accessed 2026-10-21"),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("T350", "max_power_consumption_w", "number", 17.57, "T350c/T350d 802.3at full-function maxima: 13.24W / 17.57W", "Power"),
    i("T350", "dimensions_mm", "text", "162.3 x 194.9 x 80.9 mm (T350c); 162.3 x 213.7 x 80.9 mm (T350d)", "T350c size: 162.3 x 194.9 x 80.9mm; T350d size: 162.3 x 213.7 x 80.9mm", "Physical Characteristics"),
    i("T350", "operating_temperature_c", "text", "-20 to 65 °C (T350c); -40 to 65 °C (T350d)", "Operating Temperature: T350c -20°C to 65°C; T350d -40°C to 65°C", "Physical Characteristics"),
    i("T350se", "max_power_consumption_w", "number", 21.3, "T350se 802.3at Class 4 full-function maximum power: 21.3W", "Power"),
    i("T350se", "antenna_gain_dbi", "text", "6 dBi (2.4 GHz); 8 dBi (5 GHz)", "T350se Antenna Gain (max): 2.4GHz 6dBi; 5GHz 8dBi", "RF"),
    i("T670", "max_power_consumption_w", "number", 33, "Power Consumption: DC Power 33W; 802.3bt/PoH/uPoE 33W", "Power Consumption"),
    i("R350", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "Radio Management / Wi-Fi"),
    i("R550", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "Radio Management / Wi-Fi"),
    i("H350", "poe_output", "text", "None; two data-only 1 GbE LAN ports", "Physical Interfaces: 1x 1GbE PoE In (802.3af Class 3) and 2x 1GbE LAN ports; no PoE-out function listed", "Physical Interfaces"),
]


class Command(BaseCommand):
    help = "Import manually verified remaining RUCKUS AP gaps from official model data sheets."

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
            product = Product.objects.filter(brand=brand, model=x["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing RUCKUS product: {x['model']}")
            doc_key = (url, version)
            if doc_key not in docs:
                docs[doc_key], _ = SourceDocument.objects.update_or_create(
                    url=url,
                    document_version=version,
                    defaults={
                        "brand": brand,
                        "product": None,
                        "document_type": SourceDocument.DocumentType.DATASHEET,
                        "title": title,
                        "region": "Global",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
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
                "source_note": "Manually verified from the latest available official RUCKUS model data sheet.",
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
                source_document=docs[doc_key],
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
