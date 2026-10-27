from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "H350": ("https://www.commscope.com/globalassets/digizuite/934650-ds-ruckus-h350.pdf", "RUCKUS H350 Data Sheet", "Official 2021 data sheet; accessed 2026-10-21"),
    "H550": ("https://webresources.commscope.com/download/assets/RUCKUS%2BH550%2BData%2BSheet/135d66f03bd311f0b0a3d2e4a07eb9db", "RUCKUS H550 Data Sheet", "Official 2026 web edition; accessed 2026-10-21"),
    "T750": ("https://webresources.commscope.com/download/assets/RUCKUS%2BT750%2BData%2BSheet/b363d8c63bd511f0b896d2e4a07eb9db", "RUCKUS T750 Data Sheet", "Official RUCKUS T750 data sheet; accessed 2026-10-21"),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("H350", "max_channel_width_mhz", "number", 80, "Channelization: 20, 40, 80 MHz", "Wi-Fi"),
    i("H350", "max_ssids", "number", 16, "SSID: 8 per radio (16 total across two radios)", "Performance and Capacity"),
    i("H350", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("H550", "max_ssids", "number", 16, "SSID: 8 per radio (16 total across two radios)", "Performance and Capacity"),
    i("H550", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),

    i("T750", "power_method", "text", "AC power; IEEE 802.3at or 802.3bt Class 7 PoE", "Power modes: AC, 802.3bt Class 7, or 802.3at reduced-function mode", "Power"),
    i("T750", "centralized_management", "text", "SmartZone; ZoneDirector; Cloud; Unleashed; Standalone", "Controller support: SmartZone, ZoneDirector, Cloud, Unleashed, Standalone", "Networking"),
    i("T750", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("T750", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "SmartRoam and IEEE 802.11r/k/v mobility features", "RUCKUS Radio Management / Wi-Fi"),
    i("T750", "wireless_security", "text", "WPA2/WPA3 Personal and Enterprise; Enhanced Open; Passpoint", "Wi-Fi Alliance: WPA2/WPA3 Personal and Enterprise, Enhanced Open, Passpoint", "Certifications and Compliance"),
    i("T750", "max_power_consumption_w", "number", 64.6, "Maximum listed AC consumption with Ethernet backhaul: 64.6 W", "Power"),
    i("T750", "dimensions_mm", "text", "346.4 x 240.6 x 101.7 mm", "T750 Physical Size: 34.64 x 24.06 x 10.17 cm", "Physical Characteristics"),
    i("T750", "operating_temperature_c", "text", "-40 to 65 °C", "Operating Temperature: -40°C to 65°C", "Physical Characteristics"),
    i("T750", "ip_rating", "text", "IP67", "T750 is IP-67 rated for outdoor deployments", "Product description / Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS H350/H550 late gaps and T750 specifications."

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
