from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL = "https://www.ruijie.com/pt-br/products/wireless/scenario-based-wireless/rg-map852-sf-s"
VALUES = {
    "dimensions_mm": ("text", "86 x 160 x 30 mm (W x H x D)", "Unit dimensions: 86 mm x 160 mm x 30 mm"),
    "ethernet_interfaces": (
        "text",
        "1 x 1000BASE-X LC uplink + 1 x 10/100/1000BASE-T downlink + 1 x Micro-USB console",
        "Fixed ports: 1000BASE-X LC uplink, Gigabit RJ45 downlink, Micro USB console",
    ),
    "max_clients": ("number", 256, "Maximum associated STAs: 256, up to 128 per radio"),
    "rate_2g_mbps": ("number", 574, "Radio 1, 2.4 GHz: 574 Mbps"),
    "rate_5g_mbps": ("number", 1201, "Radio 2, 5 GHz: 1.201 Gbps"),
    "antenna_gain_dbi": (
        "text", "2.4 GHz: 4.72 dBi; 5 GHz: 6.12 dBi",
        "Peak antenna gain: 4.72 dBi at 2.4 GHz and 6.12 dBi at 5 GHz",
    ),
    "antenna_type": (
        "text", "Built-in omnidirectional antennas (2 per band)",
        "Two built-in omnidirectional antennas at 2.4 GHz and two at 5 GHz",
    ),
    "fast_roaming": ("text", "Layer 2 and Layer 3 roaming", "Wireless roaming: Layer 2 and Layer 3 roaming"),
    "wireless_security": (
        "text",
        "WEP; WPA/WPA2 Personal and Enterprise; WPA3 Personal and Enterprise; WIDS; rogue AP containment",
        "Authentication/encryption includes WEP, WPA, WPA2, WPA3; WIDS and rogue AP detection/containment",
    ),
    "centralized_management": (
        "text", "WIS cloud; Wi-Fi Moho; wireless controller via CAPWAP",
        "Unified cloud management; WIS cloud; Wi-Fi Moho; IPv4/IPv6 CAPWAP and automatic AC discovery",
    ),
    "power_method": (
        "text", "48 V DC/0.5 A or IEEE 802.3af PoE via hybrid cable",
        "Input: 48 V DC/0.5 A; IEEE 802.3af-compliant PoE power input using hybrid cables",
    ),
}
CLEAR_TO_UNKNOWN = {
    "wireless_range": "Existing value was an altitude derating sentence fragment, not wireless range.",
}


class Command(BaseCommand):
    help = "Import/correct manually verified Ruijie RG-MAP852-SF-S specs stored under Reyee (round 23)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        product = Product.objects.filter(brand=brand, model="RG-MAP852", is_published=True).first()
        if not product:
            raise CommandError("Missing published Reyee product: RG-MAP852")
        codes = set(VALUES) | set(CLEAR_TO_UNKNOWN)
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Current RG-MAP852-SF-S official product page, accessed 2026-10-21",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "RG-MAP852-SF-S official product page and specification table",
                "region": "Brazil / globally applicable hardware specifications",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        written = new = corrected = unchanged = cleared = 0
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((old.value_text or "").strip()) or old.value_number is not None
                or old.value_boolean is not None
            ))
            old_value = None if not had else (old.value_number if kind == "number" else old.value_text)
            new_value = Decimal(str(value)) if kind == "number" else str(value)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "" if kind == "number" else str(value),
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the current official Ruijie product page.",
                    "verified_date": accessed,
                },
            )
            if not had:
                new += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Specifications / Hardware / Wi-Fi Radio / Software",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1

        for code, note in CLEAR_TO_UNKNOWN.items():
            definition = definitions[code]
            spec = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(spec and spec.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((spec.value_text or "").strip()) or spec.value_number is not None
                or spec.value_boolean is not None
            ))
            if had:
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""
                spec.value_number = None
                spec.value_boolean = None
                spec.normalized_value = ""
                spec.raw_value = ""
                spec.source_url = ""
                spec.source_note = f"Manual source audit: {note}"
                spec.verified_date = accessed
                spec.save()
                spec.evidence.all().delete()
                cleared += 1
            else:
                unchanged += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"cleared_bad_values={cleared} unchanged={unchanged} models=1"
        ))
