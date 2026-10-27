from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


PRODUCTS = {
    "DS-3WF02C-5AC/O": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000050901/DS-3WF02C-5AC_O_V3_Datasheet_20250731.pdf",
        "version": "V3 2025-07-31",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(867), "max_channel_width_mhz": n(80),
            "antenna_type": t("Built-in 2x2 MIMO directional antenna"), "antenna_gain_dbi": t("12 dBi"),
            "beamwidth": t("Horizontal 35°; vertical 35° (3 dB)"), "wireless_range": t("Up to 5 km"),
            "bridge_modes": t("Access point/CPE; point-to-point; point-to-multipoint"), "max_bridge_pairs": n(8),
            "ethernet_interfaces": t("2 x 10/100/1000 Mbps RJ45"), "poe_input": t("12-24 V DC passive PoE"),
            "max_power_consumption_w": n(4.5), "ip_rating": t("IP55"),
            "operating_temperature_c": t("-30 to 70 °C"), "dimensions_mm": t("90.8 x 187.8 x 57.8 mm"),
        },
    },
    "DS-3WF02C-5N/O": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000061/S000000056/OFR000075/M000011104/Data_Sheet/Datasheet-of-DS-3WF02C-5NO-Outdoor-Wireless-Bridge-Datasheet.pdf",
        "version": "Official exact-model datasheet",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(300), "max_channel_width_mhz": n(40),
            "antenna_type": t("Built-in directional antenna"), "antenna_gain_dbi": t("10 dBi"),
            "beamwidth": t("Horizontal 60°; vertical 16°"),
            "ethernet_interfaces": t("2 x 10/100 Mbps Base-TX"), "poe_input": t("24 V, 0.5 A passive PoE; up to 60 m"),
            "max_power_consumption_w": n(9.1), "operating_temperature_c": t("-30 to 75 °C"),
            "dimensions_mm": t("200 x 98.8 x 45.5 mm"),
        },
    },
    "DS-3WF03C-5AC/O": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000050902/DS-3WF03C-5AC_O_Datasheet_20260305.pdf",
        "version": "2026-03-05",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(867), "max_channel_width_mhz": n(80),
            "antenna_type": t("Built-in 2x2 MIMO directional antenna"), "antenna_gain_dbi": t("12 dBi"),
            "beamwidth": t("Horizontal 35°; vertical 35° (3 dB)"), "wireless_range": t("Up to 15 km"),
            "bridge_modes": t("Access point/CPE; point-to-point; point-to-multipoint"), "max_bridge_pairs": n(8),
            "ethernet_interfaces": t("2 x 10/100/1000 Mbps RJ45"), "poe_input": t("12-24 V DC, 1 A passive PoE"),
            "max_power_consumption_w": n(7.5), "ip_rating": t("IP55"),
            "operating_temperature_c": t("-30 to 70 °C"), "dimensions_mm": t("92 x 187 x 58 mm"),
        },
    },
    "DS-3WF0EC-2NT": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000152562/de-de/DS-3WF0EC-2NT_Datasheet_20250425.pdf",
        "version": "2025-04-25",
        "values": {
            "supported_bands": t("2.4 GHz"), "rate_2g_mbps": n(300), "max_channel_width_mhz": n(40),
            "antenna_type": t("Built-in 2x2 MIMO directional antenna"), "antenna_gain_dbi": t("7 dBi"),
            "beamwidth": t("Horizontal 65°; vertical 65° (3 dB)"), "wireless_range": t("Up to 500 m"),
            "bridge_modes": t("Point-to-point elevator bridge; AP/ST paired operation"),
            "ethernet_interfaces": t("2 x 10/100 Mbps RJ45"), "poe_input": t("12-24 V DC passive PoE"),
            "max_power_consumption_w": n(3.7), "ip_rating": t("IP55"),
            "operating_temperature_c": t("-30 to 70 °C"), "dimensions_mm": t("90.8 x 57.87 x 187.87 mm"),
        },
    },
    "DS-3WF0FA-5AC/O": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000119920/DS-3WF0FA-5AC_O_Datasheet_20260305.pdf",
        "version": "2026-03-05",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(867), "max_channel_width_mhz": n(80),
            "antenna_type": t("Built-in 2x2 MIMO omnidirectional antenna"), "antenna_gain_dbi": t("10 dBi"),
            "beamwidth": t("Horizontal 360°; vertical 8° (3 dB)"), "wireless_range": t("Up to 1 km"),
            "bridge_modes": t("Access point/CPE; point-to-point; point-to-multipoint"), "max_bridge_pairs": n(8),
            "ethernet_interfaces": t("2 x 10/100/1000 Mbps RJ45"), "poe_input": t("48 V PoE or IEEE 802.3af, 36-57 V"),
            "max_power_consumption_w": n(4.5), "ip_rating": t("IP55"),
            "operating_temperature_c": t("-30 to 60 °C"), "dimensions_mm": t("103.6 x 58.3 x 198.4 mm"),
        },
    },
    "DS-3WF5000S-SI-5ACG/2P": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000171173/DS-3WF5000S-SI-5ACG_2P_Datasheet_20260527.pdf",
        "version": "2026-05-27",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(867), "max_channel_width_mhz": n(80),
            "antenna_type": t("Built-in 2x2 MIMO directional antenna"), "antenna_gain_dbi": t("16 dBi"),
            "beamwidth": t("Horizontal 32°; vertical 17° (3 dB)"), "wireless_range": t("Up to 5 km"),
            "bridge_modes": t("Point-to-point; point-to-multipoint"), "max_bridge_pairs": n(8),
            "ethernet_interfaces": t("3 x 100/1000 Mbps RJ45; two IEEE 802.3af PoE-out ports"),
            "poe_input": t("48 V passive PoE or 12-24 V DC"), "max_power_consumption_w": n(7.7),
            "ip_rating": t("IP55"), "operating_temperature_c": t("-30 to 65 °C"),
            "dimensions_mm": t("134.21 x 235.0 x 58.73 mm"),
        },
    },
    "DS-3WFB-S-5ACG": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000175012/DS-3WFB-S-5ACG_Datasheet_20260305.pdf",
        "version": "2026-03-05",
        "values": {
            "supported_bands": t("5 GHz"), "rate_5g_mbps": n(867), "max_channel_width_mhz": n(80),
            "antenna_type": t("External optional 120° directional or 360° omnidirectional MIMO antenna"),
            "beamwidth": t("120° directional or 360° omnidirectional, depending on optional antenna"),
            "wireless_range": t("Up to 5 km"), "bridge_modes": t("Point-to-multipoint base station"),
            "max_bridge_pairs": n(32), "ethernet_interfaces": t("1 x 10/100/1000 Mbps RJ45"),
            "poe_input": t("48 V, 0.5 A PoE"), "max_power_consumption_w": n(12), "ip_rating": t("IP55"),
            "operating_temperature_c": t("-40 to 65 °C"), "dimensions_mm": t("220 x 110 x 44 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Hikvision wireless-bridge specifications (round 3)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Hikvision").first()
        if not brand:
            raise CommandError("Missing brand: Hikvision")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Hikvision product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"], document_version=item["version"],
                defaults={"brand": brand, "product": product, "document_type": SourceDocument.DocumentType.DATASHEET,
                          "title": f"Hikvision {model} official datasheet", "region": "Global", "published_date": None,
                          "accessed_date": accessed, "active": True},
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and
                           (bool((existing.value_text or "").strip()) or existing.value_number is not None or
                            existing.value_boolean is not None))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean)
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                            "value_boolean": None, "normalized_value": str(value), "unit": definition.unit,
                            "raw_value": raw, "source_url": item["url"][:200],
                            "source_note": "Manually verified from Hikvision's official exact-model datasheet; newer version preferred where available.",
                            "verified_date": accessed}
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=document,
                    source_location=f"Official datasheet specification table - {model} - {code}",
                    defaults={"source_excerpt": f"{definition.display_name}: {raw}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()},
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"))
        self.stdout.write("; ".join(per_model))
