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
    "DS-3WAP6118-EI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000177244/DS-3WAP6118-EI_Datasheet_20260228.pdf",
        "version": "2026-02-28",
        "values": {
            "total_spatial_streams": n(4, "Dual radio, four spatial streams"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1201),
            "max_clients": n(256),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 2.4 dBi; 5 GHz: 2.5 dBi"),
            "max_power_consumption_w": n(13),
            "centralized_management": t("Cloud service and app management; web/SSH; local and online upgrade"),
            "fast_roaming": t("Wireless roaming; roaming-sensitivity adjustment"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("86 x 86 x 40.6 mm"),
        },
    },
    "DS-3WAP6618-EI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000177246/DS-3WAP6618-EI_Datasheet_20260228.pdf",
        "version": "2026-02-28",
        "values": {
            "total_spatial_streams": n(4, "Dual radio, four spatial streams"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1201),
            "max_clients": n(256),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi; 5 GHz: 5.1 dBi"),
            "centralized_management": t("Cloud service and app management; web/SSH; local and online upgrade"),
            "fast_roaming": t("Wireless roaming; roaming-sensitivity adjustment"),
            "operating_temperature_c": t("-30 to 65 °C"),
            "dimensions_mm": t("240 mm diameter x 200 mm depth, excluding bracket"),
        },
    },
    # The source workbook omitted the current model's "-EI" token.  Its stored
    # official URL and Hikvision's current brochure both identify this record as
    # DS-3WF500T-EI-2N/P, so the current exact-model datasheet is used here.
    "DS-3WF500T-2N/P": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000169277/DS-3WF500T-EI-2N_P_Datasheet_20260305.pdf",
        "version": "Current model DS-3WF500T-EI-2N/P, 2026-03-05",
        "values": {
            "rate_2g_mbps": n(300, "Max. transmission rate: <= 300 Mbps"),
            "max_channel_width_mhz": n(40, "10/20/40 MHz"),
            "antenna_type": t("Built-in 2x2 MIMO directional antenna"),
            "antenna_gain_dbi": t("7 dBi"),
            "beamwidth": t("Horizontal 60°; vertical 50° (3 dB)"),
            "wireless_range": t("Up to 500 m"),
            "bridge_modes": t("Elevator point-to-point bridge; AP/CPE paired operation"),
            "ethernet_interfaces": t("2 x 10/100 Mbps RJ45"),
            "poe_input": t("AP: IEEE 802.3af/at PoE input; CPE: passive PoE input and IEEE 802.3af PoE output"),
            "max_power_consumption_w": n(3.4),
            "ip_rating": t("IP55"),
            "operating_temperature_c": t("-30 to 60 °C"),
            "dimensions_mm": t("90.8 x 187.87 x 57.87 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Hikvision AP and wireless-bridge specifications (round 4)."

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
                url=item["url"],
                document_version=item["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Hikvision {model} official datasheet",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                old_value = None
                if had:
                    old_value = (
                        existing.value_text
                        if existing.value_text
                        else existing.value_number
                        if existing.value_number is not None
                        else existing.value_boolean
                    )

                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from Hikvision's current official exact-model datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)

                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                if not had:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1

                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=document,
                    source_location=f"Official datasheet specification table - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1

            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
