from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/RUCKUS%2BR575%2BData%2BSheet/9f88997e603a11f19ca57a92be02af9a"
SOURCE_TITLE = "RUCKUS R575 Data Sheet"
SOURCE_VERSION = "PA-300177.1-EN (08/26); accessed 2026-10-21"


def i(code, kind, value, raw, location):
    return {"code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("total_spatial_streams", "number", 6, "6 spatial streams (2x2:2 across 2.4GHz, 5GHz, and 6GHz)", "Overview"),
    i("mimo_2g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("mimo_5g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("mimo_6g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("rate_2g_mbps", "number", 689, "Peak PHY Rates: 2.4 GHz: 689 Mbps", "Performance and Capacity"),
    i("rate_5g_mbps", "number", 2882, "Peak PHY Rates: 5 GHz: 2882 Mbps", "Performance and Capacity"),
    i("rate_6g_mbps", "number", 5765, "Peak PHY Rates: 6 GHz: 5765 Mbps", "Performance and Capacity"),
    i("max_channel_width_mhz", "number", 320, "Channelization: 20, 40, 80, 160, 320 MHz", "Wi-Fi"),
    i("antenna_type", "text", "BeamFlex+ adaptive antennas with polarization diversity", "Antenna Type: BeamFlex+ adaptive antennas with polarization diversity; 4,000+ patterns per band", "RF"),
    i("antenna_gain_dbi", "text", "Up to 4 dBi", "Antenna Gain (max): Up to 4dBi", "RF"),
    i("max_clients", "number", 512, "Client Capacity: 512 clients per AP", "Performance and Capacity"),
    i("ethernet_interfaces", "text", "2 x 2.5/1 GbE (one PoE-in; LAG supported)", "Two 100M/1/2.5GbE ports, one with PoE in; link aggregation supported", "Physical Interfaces / Overview"),
    i("power_method", "text", "IEEE 802.3at PoE+; IEEE 802.3af PoE", "Power Supply Mode: 802.3at or 802.3af; no DC power jack", "Power Requirements / Ordering"),
    i("max_power_consumption_w", "number", 25.5, "802.3at maximum power: 25.5W", "Power Requirements"),
    i("centralized_management", "text", "SmartZone; RUCKUS Unleashed; RUCKUS One", "Controller Platform Support: SmartZone, RUCKUS Unleashed, RUCKUS One with agentic AI", "Networking"),
    i("mesh_support", "boolean", True, "Mesh: SmartMesh wireless meshing technology; self-healing mesh in 2.4, 5 and 6 GHz", "Networking"),
    i("fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "Radio Management / Wi-Fi"),
    i("wireless_security", "text", "WPA2/WPA3 Personal and Enterprise; OWE; DPSK3; WIPS/WIDS; TPM 2.0; Secure Boot", "Security: WPA2 AES, WPA3-Personal, WPA3-Enterprise, OWE, DPSK3, WIPS/WIDS, TPM 2.0, Secure Boot", "Wi-Fi"),
    i("dimensions_mm", "text", "198.5 x 198.5 x 48.5 mm", "Physical Size: 19.85cm x 19.85cm x 4.85cm", "Physical Characteristics"),
    i("operating_temperature_c", "text", "0 to 50 °C", "Operating Temperature: 0ºC (32ºF) to 50ºC (122ºF) ambient", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS R575 specifications and corrections from the latest official 2026 data sheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        product = Product.objects.filter(brand=brand, model="R575", is_published=True).first()
        if not product:
            raise CommandError("Missing RUCKUS product: R575")
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
                "source_note": "Manually verified from the latest official RUCKUS/Belden R575 data sheet.",
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
