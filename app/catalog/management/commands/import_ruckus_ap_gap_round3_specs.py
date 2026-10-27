from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "H510": ("https://www.commscope.com/globalassets/digizuite/764504-pa-114282-en-ds-ruckus-h510.pdf", "RUCKUS H510 Data Sheet", "PA-114282-EN official data sheet; accessed 2026-10-21"),
    "T350": ("https://webresources.commscope.com/download/assets/RUCKUS%2BT350%2BData%2BSheet/f6e7d1ea3bd711f097831adcaa92e24e", "RUCKUS T350 Data Sheet", "Official 2025 web edition; accessed 2026-10-21"),
}


def i(model, code, kind, value, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "location": location}


ITEMS = [
    i("H510", "supported_bands", "text", "2.4 GHz / 5 GHz", "Dual-band 2.4 GHz and 5 GHz 802.11ac Wave 2 access point", "Product description / Wi-Fi"),
    i("H510", "total_spatial_streams", "number", 4, "2x2:2 on each of two concurrent radios", "Wi-Fi"),
    i("H510", "rate_2g_mbps", "number", 300, "Peak PHY rate: 2.4 GHz 300 Mbps", "Performance and Capacity"),
    i("H510", "rate_5g_mbps", "number", 867, "Peak PHY rate: 5 GHz 867 Mbps", "Performance and Capacity"),
    i("H510", "max_clients", "number", 100, "Client capacity: up to 100 clients per AP", "Performance and Capacity"),
    i("H510", "mimo_2g", "text", "2 x 2:2", "Radio chains and streams: 2x2:2", "Wi-Fi"),
    i("H510", "mimo_5g", "text", "2 x 2:2", "Radio chains and streams: 2x2:2", "Wi-Fi"),
    i("H510", "max_ssids", "number", 16, "SSID: up to 16 per AP", "Performance and Capacity"),
    i("H510", "ethernet_interfaces", "text", "5 x 1GbE RJ45 (1 x uplink, 4 x LAN; one LAN supports PoE output)", "1 x 1GbE RJ-45 uplink; 4 x 1GbE LAN ports, one PoE-out", "Physical Interfaces"),
    i("H510", "power_method", "text", "IEEE 802.3af/at PoE", "Power supply: 802.3af/802.3at", "Power"),
    i("H510", "poe_output", "text", "1 x PoE output LAN port", "Four LAN ports, one PoE-out", "Physical Interfaces"),
    i("H510", "max_power_consumption_w", "number", 12.9, "Maximum power consumption: 12.9 W", "Power"),
    i("H510", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud Wi-Fi; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud Wi-Fi, Standalone", "Networking"),
    i("H510", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "Mobility: SmartRoam; Other Wi-Fi Features: 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("H510", "wireless_security", "text", "WPA/WPA2; AES; 802.11i; Dynamic PSK; WIPS/WIDS", "Security: WPA-PSK, WPA-TKIP, WPA2 AES, 802.11i, Dynamic PSK; WIPS/WIDS", "Wi-Fi"),
    i("H510", "operating_temperature_c", "text", "0 to 40 °C", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),
    i("H510", "dimensions_mm", "text", "90 x 171 x 29 mm", "Physical Size: 90 mm (W) x 171 mm (L) x 29 mm (H)", "Physical Characteristics"),

    i("T350", "power_method", "text", "IEEE 802.3af/at PoE", "Common input: 1 x 1GbE RJ-45 PoE In, 802.3at Class 4; 802.3af mode supported", "Physical Interfaces / Power"),
    i("T350", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; Cloud; Standalone", "Controller support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    i("T350", "mesh_support", "boolean", True, "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    i("T350", "fast_roaming", "text", "SmartRoam; IEEE 802.11r/k/v", "SmartRoam and IEEE 802.11r/k/v", "RUCKUS Radio Management / Wi-Fi"),
    i("T350", "wireless_security", "text", "WPA3 Enterprise/Personal; Enhanced Open; Passpoint", "Wi-Fi Alliance: WPA3 Enterprise/Personal, Enhanced Open, Passpoint", "Certifications and Compliance"),
    i("T350", "ip_rating", "text", "IP67", "Ingress Protection: IP-67 for all T350 variants", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS H510 and common T350-family access-point gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand: raise CommandError("Missing brand: RUCKUS")
        codes = {x["code"] for x in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys(): raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate(); documents = {}; newly_filled = corrected = unchanged = 0
        for x in ITEMS:
            url, title, version = SOURCES[x["model"]]
            if x["model"] not in documents:
                documents[x["model"]], _ = SourceDocument.objects.update_or_create(
                    url=url, document_version=version,
                    defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                              "title": title, "region": "Global", "published_date": None,
                              "accessed_date": accessed, "active": True})
            product = Product.objects.filter(brand=brand, model=x["model"], is_published=True).first()
            if not product: raise CommandError(f"Missing RUCKUS product: {x['model']}")
            definition = definitions[x["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
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
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[x["model"]], source_location=x["location"],
                defaults={"source_excerpt": x["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                          "verified_at": timezone.now()})
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"))
