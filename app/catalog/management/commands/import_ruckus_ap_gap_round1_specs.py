from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "GUIDE": {
        "url": "https://www.commscope.com/globalassets/digizuite/62228-ruckus-product-guide.pdf",
        "title": "RUCKUS Product Guide",
        "version": "Official RUCKUS product guide, 2024; accessed 2026-10-21",
    },
    "H350": {
        "url": "https://www.commscope.com/globalassets/digizuite/934650-ds-ruckus-h350.pdf",
        "title": "RUCKUS H350 Data Sheet",
        "version": "Official RUCKUS H350 data sheet; accessed 2026-10-21",
    },
    "H550": {
        "url": "https://webresources.commscope.com/download/assets/RUCKUS%2BH550%2BData%2BSheet/135d66f03bd311f0b0a3d2e4a07eb9db",
        "title": "RUCKUS H550 Data Sheet",
        "version": "Official RUCKUS H550 data sheet, 2026 web edition; accessed 2026-10-21",
    },
    "R350": {
        "url": "https://webresources.commscope.com/download/assets/RUCKUS%2BR350%2BData%2BSheet/ccf181263bd511f099f1068e18034550",
        "title": "RUCKUS R350 Data Sheet",
        "version": "Official RUCKUS R350 data sheet, 2025 web edition; accessed 2026-10-21",
    },
    "R550": {
        "url": "https://webresources.commscope.com/download/assets/RUCKUS%2BR550%2BData%2BSheet/4378f5643bd511f0a4acea1fa90d937b",
        "title": "RUCKUS R550 Data Sheet",
        "version": "Official RUCKUS R550 data sheet, 2025 web edition; accessed 2026-10-21",
    },
}


def item(model, code, kind, value, source, raw, location):
    return {"model": model, "code": code, "kind": kind, "value": value, "source": source, "raw": raw, "location": location}


ITEMS = [
    item("H350", "total_spatial_streams", "number", 4, "GUIDE", "Radio chains:streams: 2x2:2 on 2.4 GHz and 2x2:2 on 5 GHz", "Indoor access points comparison — H350"),
    item("H350", "rate_2g_mbps", "number", 574, "GUIDE", "Maximum PHY rate: 574 Mbps (2.4 GHz)", "Indoor access points comparison — H350"),
    item("H350", "rate_5g_mbps", "number", 1200, "GUIDE", "Maximum PHY rate: 1200 Mbps (5 GHz)", "Indoor access points comparison — H350"),
    item("H350", "max_clients", "number", 512, "GUIDE", "Concurrent users: 512", "Indoor access points comparison — H350"),
    item("H350", "mimo_2g", "text", "2 x 2:2", "GUIDE", "Radio chains:streams (MU-MIMO): 2x2:2", "Indoor access points comparison — H350"),
    item("H350", "mimo_5g", "text", "2 x 2:2", "GUIDE", "Radio chains:streams (MU-MIMO): 2x2:2", "Indoor access points comparison — H350"),
    item("H350", "ethernet_interfaces", "text", "3 x 1GbE RJ45 (1 x PoE input, 2 x LAN)", "H350", "1x 1GbE RJ-45 PoE In; 2x 1GbE RJ-45 LAN ports", "Physical Interfaces"),
    item("H350", "power_method", "text", "IEEE 802.3af PoE", "H350", "Power mode: 802.3af", "Power Configuration Options"),
    item("H350", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; RUCKUS Cloud; Standalone", "H350", "Controller Platform Support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    item("H350", "wireless_security", "text", "WPA3 Enterprise/Personal; Enhanced Open; Passpoint", "H350", "Wi-Fi Alliance: WPA3 Enterprise Personal; Wi-Fi Enhanced Open; Passpoint", "Certifications and Compliance"),
    item("H350", "max_power_consumption_w", "number", 12.54, "H350", "Power Consumption: 12.54 W", "Power Configuration Options"),
    item("H350", "dimensions_mm", "text", "89.5 x 178.5 x 29.3 mm", "H350", "Physical Size: 89.5 mm (W) x 178.5 mm (L) x 29.3 mm (H)", "Physical Characteristics"),
    item("H350", "operating_temperature_c", "text", "0 to 40 °C", "H350", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),

    item("H550", "total_spatial_streams", "number", 4, "GUIDE", "Radio chains:streams: 2x2:2 on 2.4 GHz and 2x2:2 on 5 GHz", "Indoor access points comparison — H550"),
    item("H550", "rate_2g_mbps", "number", 574, "GUIDE", "Maximum PHY rate: 574 Mbps (2.4 GHz)", "Indoor access points comparison — H550"),
    item("H550", "rate_5g_mbps", "number", 1200, "GUIDE", "Maximum PHY rate: 1200 Mbps (5 GHz)", "Indoor access points comparison — H550"),
    item("H550", "max_clients", "number", 512, "GUIDE", "Concurrent users: 512", "Indoor access points comparison — H550"),
    item("H550", "mimo_2g", "text", "2 x 2:2", "GUIDE", "Radio chains:streams (MU-MIMO): 2x2:2", "Indoor access points comparison — H550"),
    item("H550", "mimo_5g", "text", "2 x 2:2", "GUIDE", "Radio chains:streams (MU-MIMO): 2x2:2", "Indoor access points comparison — H550"),
    item("H550", "ethernet_interfaces", "text", "5 x 1GbE RJ45 (1 x PoE input, 4 x LAN; one LAN supports PoE output)", "H550", "1x 1GbE RJ-45 PoE In; 4x 1GbE RJ-45 LAN ports, one PoE Out", "Physical Interfaces"),
    item("H550", "power_method", "text", "IEEE 802.3af/at/bt PoE; Cisco UPOE; PoH", "H550", "Power modes: 802.3af, 802.3at, 802.3bt, uPoE, PoH", "Power Configuration Options"),
    item("H550", "poe_output", "text", "1 x PoE output: IEEE 802.3af or 48 V passive PoE (SKU-dependent)", "H550", "One PoE Out port — 802.3af (901-H550-XX00) or 48V passive PoE (901-H550-XX02)", "Physical Interfaces"),
    item("H550", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; RUCKUS Cloud; Standalone", "H550", "Controller Platform Support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    item("H550", "wireless_security", "text", "WPA3 Enterprise/Personal; Enhanced Open; Passpoint", "H550", "Wi-Fi Alliance: WPA3 Enterprise Personal; Wi-Fi Enhanced Open; Passpoint", "Certifications and Compliance"),
    item("H550", "max_power_consumption_w", "number", 32.21, "H550", "Maximum listed power consumption: 32.21 W with full 802.3bt/uPoE/PoH functionality", "Power Configuration Options"),
    item("H550", "dimensions_mm", "text", "89.5 x 178.5 x 29.3 mm", "H550", "Physical Size: 89.5 mm (W) x 178.5 mm (L) x 29.3 mm (H)", "Physical Characteristics"),
    item("H550", "operating_temperature_c", "text", "0 to 40 °C", "H550", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),

    item("R350", "power_method", "text", "IEEE 802.3af PoE; 12 VDC", "R350", "Power supply: PoE or DC input", "Power"),
    item("R350", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; RUCKUS Cloud; Standalone", "R350", "Controller Platform Support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    item("R350", "mesh_support", "boolean", True, "R350", "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    item("R350", "max_power_consumption_w", "number", 12.62, "R350", "PoE full functionality maximum power consumption: 12.62 W", "Power"),
    item("R350", "dimensions_mm", "text", "146.0 x 155.9 x 39.3 mm", "R350", "Physical Size: 14.60 (L) x 15.59 (W) x 3.93 (H) cm", "Physical Characteristics"),
    item("R350", "operating_temperature_c", "text", "0 to 40 °C", "R350", "Operating Temperature: 0°C to 40°C", "Physical Characteristics"),

    item("R550", "power_method", "text", "IEEE 802.3af/at PoE; 12 VDC", "R550", "Power supply: 802.3af PoE, 802.3at PoE+, or 12VDC input", "Power"),
    item("R550", "centralized_management", "text", "SmartZone; ZoneDirector; Unleashed; RUCKUS Cloud; Standalone", "R550", "Controller Platform Support: SmartZone, ZoneDirector, Unleashed, Cloud, Standalone", "Networking"),
    item("R550", "mesh_support", "boolean", True, "R550", "SmartMesh wireless meshing technology; self-healing mesh", "Networking"),
    item("R550", "max_power_consumption_w", "number", 18.71, "R550", "PoE+ full functionality maximum power consumption: 18.71 W", "Power"),
    item("R550", "dimensions_mm", "text", "176.0 x 190.2 x 47.8 mm", "R550", "Physical Size: 17.60 cm (L) x 19.02 cm (W) x 4.78 cm (H)", "Physical Characteristics"),
    item("R550", "operating_temperature_c", "text", "0 to 50 °C", "R550", "Operating Temperature: 0°C to 50°C", "Physical Characteristics"),
]


class Command(BaseCommand):
    help = "Import manually verified RUCKUS H350/H550/R350/R550 access-point gap specifications."

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
            src = SOURCES[entry["source"]]
            key = (src["url"], src["version"])
            if key not in documents:
                documents[key], _ = SourceDocument.objects.update_or_create(
                    url=src["url"], document_version=src["version"],
                    defaults={
                        "brand": brand, "product": None,
                        "document_type": SourceDocument.DocumentType.DATASHEET,
                        "title": src["title"], "region": "Global",
                        "published_date": None, "accessed_date": accessed, "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=entry["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing RUCKUS product: {entry['model']}")
            definition = definitions[entry["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
            ))
            if entry["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(entry["value"]))
            elif entry["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(entry["value"])
            else:
                old_value = existing.value_text if had else None
                new_value = str(entry["value"])
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(entry["value"]), "unit": definition.unit,
                "raw_value": entry["raw"], "source_url": src["url"][:200],
                "source_note": "Manually verified from an official CommScope/RUCKUS product guide or data sheet; the latest identifiable edition was preferred.",
                "verified_date": accessed,
            }
            if entry["kind"] == "number":
                defaults["value_number"] = new_value
            elif entry["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[key], source_location=entry["location"],
                defaults={
                    "source_excerpt": entry["raw"],
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
