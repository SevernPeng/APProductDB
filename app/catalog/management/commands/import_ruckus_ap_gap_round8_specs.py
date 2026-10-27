from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/Datasheet:%2BRUCKUS%2BH670/48669c9cd7a311f0a98566254722ed67"
SOURCE_TITLE = "RUCKUS H670 Data Sheet"
SOURCE_VERSION = "PA-120271.3-EN (09/26); accessed 2026-10-21"


def i(code, kind, value, raw, location):
    return {"code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("total_spatial_streams", "number", 6, "6 spatial streams (2x2:2 in 2.4GHz, 5GHz, and 6GHz)", "Overview"),
    i("mimo_2g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("mimo_5g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("mimo_6g", "text", "2x2:2", "Radio Chains and Streams: 2x2:2 in all 3 bands", "Wi-Fi"),
    i("rate_2g_mbps", "number", 689, "Peak PHY Rates: 2.4GHz: 689 Mbps", "Performance and Capacity"),
    i("rate_5g_mbps", "number", 2882, "Peak PHY Rates: 5GHz: 2882 Mbps", "Performance and Capacity"),
    i("rate_6g_mbps", "number", 5765, "Peak PHY Rates: 6GHz: 5765 Mbps", "Performance and Capacity"),
    i("max_channel_width_mhz", "number", 320, "Channelization: 20, 40, 80, 160, 320 MHz", "Wi-Fi"),
    i("antenna_type", "text", "BeamFlex+ adaptive antennas with polarization diversity", "Antenna Type: BeamFlex+ adaptive antennas with polarization diversity", "RF"),
    i("antenna_gain_dbi", "text", "Up to 3 dBi", "Antenna Gain (max): Up to 3dBi", "RF"),
    i("max_clients", "number", 768, "Client Capacity: Up to 768 clients per AP", "Performance and Capacity"),
    i("max_ssids", "number", 36, "SSID: Up to 36 per AP", "Performance and Capacity"),
    i("ethernet_interfaces", "text", "1 x 5/2.5/1 GbE PoE-in; 4 x 2.5/1 GbE (up to 2 PoE-out)", "Ethernet: 1x 100M/1/2.5/5GbE PoE-in; 4x 10M/100M/1/2.5GbE, up to 2x PoE-out", "Physical Interfaces"),
    i("poe_output", "text", "1 x IEEE 802.3at or 2 x IEEE 802.3af", "Power Over Ethernet Out: optional 1xAT or 2xAF with DC or 802.3bt power", "Physical Interfaces"),
    i("power_method", "text", "48 V DC; IEEE 802.3at/bt; PoH; uPoE", "DC Power: 48V; Power over Ethernet In: 802.3at/bt; PoH; uPoE", "Physical Interfaces / Power Consumption"),
    i("max_power_consumption_w", "number", 51, "802.3bt/PoH/uPoE: 45.74W average; LLDP request: 51W", "Power Consumption"),
    i("centralized_management", "text", "SmartZone; RUCKUS Unleashed; RUCKUS One", "Controller Platform Support: SmartZone, RUCKUS Unleashed, RUCKUS One", "Networking"),
    i("mesh_support", "boolean", True, "Mesh: SmartMesh wireless meshing technology; self-healing mesh in 2.4, 5 and 6 GHz", "Networking"),
    i("fast_roaming", "text", "SmartRoam", "RUCKUS Advanced RF Technology: SmartRoam; Mobility: SmartRoam", "Key Highlights / Radio Management"),
    i("wireless_security", "text", "WPA2/WPA3; WPA3-SAE; OWE; PMF (802.11w); DPSK3; WIPS/WIDS; TPM 2.0; Secure Boot", "Security: WPA2, WPA3, WPA3-SAE, OWE, PMF, DPSK3, WIPS/WIDS, TPM 2.0, Secure Boot", "Wi-Fi"),
    i("dimensions_mm", "text", "182.6 x 222.1 x 32 mm", "Physical Size: 182.6mm x 222.1mm x 32mm", "Physical Characteristics"),
    i("operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0ºC (32ºF) to 40ºC (104ºF)", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS H670 specifications from the latest official 2026 data sheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        product = Product.objects.filter(brand=brand, model="H670", is_published=True).first()
        if not product:
            raise CommandError("Missing RUCKUS product: H670")
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
                "source_note": "Manually verified from the latest official RUCKUS/Belden H670 data sheet.",
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
