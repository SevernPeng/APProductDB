from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "R310": ("https://www.commscope.com/globalassets/digizuite/61767-ds-ruckus-r310.pdf", "RUCKUS R310 Data Sheet", "Official 2020 data sheet; accessed 2026-10-21"),
    "R320": ("https://www.commscope.com/globalassets/digizuite/61768-ds-ruckus-r320.pdf", "RUCKUS R320 Data Sheet", "Official 2020 data sheet; accessed 2026-10-21"),
    "R650": ("https://webresources.commscope.com/download/assets/RUCKUS%2BR650%2BData%2BSheet/b1e01d703bd511f0aa32068e18034550", "RUCKUS R650 Data Sheet", "PA-114143.8-EN (01/26); accessed 2026-10-21"),
    "R750": ("https://webresources.commscope.com/download/assets/RUCKUS%2BR750%2BData%2BSheet/bc1a1f343bd511f0acd93e67199c332c", "RUCKUS R750 Data Sheet", "PA-114022.7-EN (12/25); accessed 2026-10-21"),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("R310", "total_spatial_streams", "number", 4, "2x2:2 on each of two concurrent radios", "Wi-Fi"),
    i("R310", "rate_2g_mbps", "number", 300, "Peak PHY rate: 2.4 GHz 300 Mbps", "Performance and Capacity"),
    i("R310", "rate_5g_mbps", "number", 867, "Peak PHY rate: 5 GHz 867 Mbps", "Performance and Capacity"),
    i("R310", "max_channel_width_mhz", "number", 80, "Channelization: 20, 40, 80 MHz", "Wi-Fi"),
    i("R310", "ethernet_interfaces", "text", "1 x 1GbE RJ45", "Ethernet: 1 x 1GbE port, RJ-45", "Physical Interfaces"),
    i("R310", "power_method", "text", "IEEE 802.3af PoE; 12 VDC", "Power supply: 802.3af or DC input 12 VDC", "Power"),
    i("R310", "max_clients", "number", 100, "Client capacity: up to 100 clients per AP", "Performance and Capacity"),
    i("R310", "mimo_2g", "text", "2 x 2:2", "Radio chains and streams: 2x2:2", "Wi-Fi"),
    i("R310", "mimo_5g", "text", "2 x 2:2", "Radio chains and streams: 2x2:2", "Wi-Fi"),
    i("R310", "antenna_type", "text", "Integrated BeamFlex adaptive antennas", "Antenna type: BeamFlex adaptive antennas", "RF"),
    i("R310", "antenna_gain_dbi", "text", "Up to 3 dBi", "Antenna gain (max): up to 3 dBi", "RF"),
    i("R310", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud Wi-Fi; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud Wi-Fi, Standalone", "Networking"),
    i("R310", "mesh_support", "boolean", False, "Mesh: No Mesh support", "Networking"),
    i("R310", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R310", "max_power_consumption_w", "number", 11, "802.3af maximum power consumption: 11 W", "Power"),
    i("R310", "dimensions_mm", "text", "138 x 135 x 33 mm", "Physical Size: 13.8 x 13.5 x 3.3 cm", "Physical Characteristics"),
    i("R310", "operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),

    i("R320", "power_method", "text", "IEEE 802.3af PoE; 12 VDC", "Power supply: 802.3af or DC input 12 VDC", "Power"),
    i("R320", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    i("R320", "mesh_support", "boolean", False, "Mesh: No Mesh support", "Networking"),
    i("R320", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R320", "max_power_consumption_w", "number", 12.18, "802.3af maximum power consumption: 12.18 W", "Power"),
    i("R320", "dimensions_mm", "text", "132 x 138 x 31 mm", "Physical Size: 13.2 x 13.8 x 3.1 cm", "Physical Characteristics"),
    i("R320", "operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),

    i("R650", "power_method", "text", "IEEE 802.3af/at PoE; DC power", "Power supply: 802.3af PoE, 802.3at PoE+, or DC power", "Power"),
    i("R650", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Standalone", "Networking"),
    i("R650", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("R650", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R650", "max_power_consumption_w", "number", 21.59, "PoE+ full-function maximum power consumption: 21.59 W", "Power"),
    i("R650", "dimensions_mm", "text", "224 x 194 x 47 mm", "Physical Size: 22.4 x 19.4 x 4.7 cm", "Physical Characteristics"),
    i("R650", "operating_temperature_c", "text", "0 to 50 °C", "Operating Temperature: 0°C to 50°C", "Physical Characteristics"),

    i("R750", "power_method", "text", "IEEE 802.3af/at/bt PoE; DC power", "Power over Ethernet: 802.3af/at/bt; DC power option", "Physical Interfaces / Power"),
    i("R750", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    i("R750", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("R750", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("R750", "max_power_consumption_w", "number", 22.69, "Maximum listed consumption: DC power 22.69 W", "Power"),
    i("R750", "dimensions_mm", "text", "235 x 206 x 62 mm", "Physical Size: 23.5 x 20.6 x 6.2 cm", "Physical Characteristics"),
    i("R750", "operating_temperature_c", "text", "0 to 50 °C", "Operating Temperature: 0°C to 50°C", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS R310/R320/R650/R750 access-point gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        codes = {entry["code"] for entry in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for entry in ITEMS:
            url, title, version = SOURCES[entry["model"]]
            if entry["model"] not in documents:
                documents[entry["model"]], _ = SourceDocument.objects.update_or_create(
                    url=url, document_version=version,
                    defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                              "title": title, "region": "Global", "published_date": None,
                              "accessed_date": accessed, "active": True},
                )
            product = Product.objects.filter(brand=brand, model=entry["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing RUCKUS product: {entry['model']}")
            definition = definitions[entry["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None))
            if entry["kind"] == "number":
                old_value, new_value = (existing.value_number if had else None), Decimal(str(entry["value"]))
            elif entry["kind"] == "boolean":
                old_value, new_value = (existing.value_boolean if had else None), bool(entry["value"])
            else:
                old_value, new_value = (existing.value_text if had else None), str(entry["value"])
            defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                        "value_boolean": None, "normalized_value": str(entry["value"]), "unit": definition.unit,
                        "raw_value": entry["raw"], "source_url": url[:200],
                        "source_note": "Manually verified from the official CommScope/RUCKUS model data sheet.",
                        "verified_date": accessed}
            if entry["kind"] == "number": defaults["value_number"] = new_value
            elif entry["kind"] == "boolean": defaults["value_boolean"] = new_value
            else: defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had: newly_filled += 1
            elif old_value != new_value: corrected += 1
            else: unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[entry["model"]], source_location=entry["location"],
                defaults={"source_excerpt": entry["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                          "verified_at": timezone.now()},
            )
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"))
