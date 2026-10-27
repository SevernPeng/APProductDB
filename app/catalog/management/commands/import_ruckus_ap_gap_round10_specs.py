from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/Data%2BSheet:%2BRUCKUS%2BR350e/d683bda2d7a311f09d5be25980888793"
SOURCE_TITLE = "RUCKUS R350e Data Sheet"
SOURCE_VERSION = "PA-118274.2-EN (01/26); accessed 2026-10-21"


def i(code, kind, value, raw, location):
    return {"code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("supported_bands", "text", "2.4 GHz / 5 GHz", "R350e dual-band (5GHz and 2.4GHz concurrent) 802.11ax", "Ordering Information"),
    i("total_spatial_streams", "number", 4, "2 streams at 5GHz and 2 streams at 2.4GHz", "Wi-Fi"),
    i("mimo_2g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 (2.4GHz)", "Wi-Fi"),
    i("mimo_5g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 (5GHz)", "Wi-Fi"),
    i("rate_2g_mbps", "number", 574, "Peak PHY Rates: 2.4GHz: 574Mbps", "Performance and Capacity"),
    i("rate_5g_mbps", "number", 1200, "Peak PHY Rates: 5GHz: 1200Mbps", "Performance and Capacity"),
    i("max_channel_width_mhz", "number", 80, "Channelization: 20, 40, 80MHz", "Wi-Fi"),
    i("antenna_gain_dbi", "text", "Up to 3 dBi", "Antenna Gain (max): Up to 3dBi", "RF"),
    i("max_clients", "number", 128, "Client Capacity: Up to 128 clients per AP", "Performance and Capacity"),
    i("max_ssids", "number", 8, "SSID: Up to 8 per AP (4 per band)", "Performance and Capacity"),
    i("ethernet_interfaces", "text", "1 x 1 GbE RJ-45", "Ethernet: 1 x 1GbE port, RJ-45", "Physical Interfaces"),
    i("power_method", "text", "PoE; 12 V DC via optional adapter", "Power supply: PoE or DC input; optional power adapter is 12V, 1.0A, 12W", "Power / Optional Accessories"),
    i("max_power_consumption_w", "number", 12.62, "PoE (Full Functionality) maximum power consumption: 12.62W", "Power"),
    i("centralized_management", "text", "RUCKUS One; SmartZone; RUCKUS Unleashed", "Controller Platform Support: RUCKUS One, SmartZone, Unleashed", "Networking"),
    i("mesh_support", "boolean", True, "Mesh: SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "Radio Management / Wi-Fi"),
    i("wireless_security", "text", "WPA2/WPA3 Personal and Enterprise; Dynamic PSK; WIPS/WIDS", "Security: WPA2, WPA3-Personal, WPA3-Enterprise, Dynamic PSK; WIPS/WIDS", "Wi-Fi"),
    i("dimensions_mm", "text", "146.0 x 155.9 x 39.3 mm", "Physical Size: 14.60(L) x 15.59(W) x 3.93(H) cm", "Physical Characteristics"),
    i("operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0ºC (32ºF) to 40ºC (104ºF)", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS R350e specifications from the latest official 2026 data sheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        product = Product.objects.filter(brand=brand, model="R350e", is_published=True).first()
        if not product:
            raise CommandError("Missing RUCKUS product: R350e")
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
                "product": product,
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
                "source_note": "Manually verified from the latest official RUCKUS R350e data sheet.",
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
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
