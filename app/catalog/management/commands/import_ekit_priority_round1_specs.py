from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


CENTRAL = "HUAWEI eKit App and SNC cloud platform; compatible Huawei wireless access controller management"

PRODUCTS = {
    "AP162E": {
        "url": "https://ekit.huawei.com/ekit/front/ssr/en/product/1480064473950643072",
        "values": {
            "total_spatial_streams": n(4), "mimo_2g": t("2x2"), "mimo_5g": t("2x2"),
            "max_channel_width_mhz": n(160, "2.4 GHz: 40 MHz; 5 GHz: 160 MHz"),
            "power_method": t("IEEE 802.3af PoE"), "max_clients": n(128),
            "ethernet_interfaces": t("2 x 10/100/1000Base-T RJ45"),
            "max_power_consumption_w": n(9.1), "dimensions_mm": t("86 x 86 x 42.5 mm"),
            "operating_temperature_c": t("0 to 40 °C"), "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi/chain peak, 3 dBi combined; 5 GHz: 2 dBi/chain peak, 1 dBi combined"),
            "wireless_range": t("15 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP265E": {
        "url": "https://ekit.huawei.com/ekit/front/ssr/en/product/1480064306648244992",
        "values": {
            "max_clients": n(128), "ethernet_interfaces": t("5 x 10/100/1000Base-T RJ45"),
            "max_power_consumption_w": n(9.4), "dimensions_mm": t("160 x 86 x 38 mm"),
            "operating_temperature_c": t("0 to 40 °C"), "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 2 dBi combined; 5 GHz: 4 dBi/chain peak, 1 dBi combined"),
            "wireless_range": t("20 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP266": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1862499490084291416",
        "values": {
            "max_clients": n(128), "ethernet_interfaces": t("5 x 10/100/1000Base-T RJ45"),
            "power_method": t("IEEE 802.3af/802.3at PoE"), "poe_output": t("Up to 15 W PoE output"),
            "max_power_consumption_w": n(9.4, "9.4 W excluding PoE output"),
            "dimensions_mm": t("160 x 86 x 38 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 2 dBi combined; 5 GHz: 4 dBi/chain peak, 1 dBi combined"),
            "wireless_range": t("20 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP271E": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1884238225671193114",
        "values": {
            "max_clients": n(256),
            "ethernet_interfaces": t("4 x 1GbE RJ45; 1 x 2.5GbE RJ45; 2 x RJ45 pass-through"),
            "power_method": t("IEEE 802.3af/802.3at PoE or 12 V DC"),
            "max_power_consumption_w": n(13.2, "13.2 W excluding USB"),
            "dimensions_mm": t("175 x 86 x 45 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 5 dBi/chain peak, 3 dBi combined; 5 GHz: 5 dBi/chain peak, 3 dBi combined"),
            "wireless_range": t("18 m optimal signal distance"),
            "fast_roaming": t("Seamless roaming with signal steering"), "centralized_management": t(CENTRAL),
        },
    },
    "AP361": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1931229518437286522",
        "values": {
            "max_channel_width_mhz": n(80, "2.4 GHz: 40 MHz; 5 GHz: 80 MHz"),
            "ethernet_interfaces": t("1 x 10/100/1000Base-T RJ45"),
            "max_power_consumption_w": n(9.4), "dimensions_mm": t("180 mm diameter x 35 mm depth"),
            "operating_temperature_c": t("0 to 40 °C"), "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 2 dBi combined; 5 GHz: 5 dBi/chain peak, 3 dBi combined"),
            "wireless_range": t("20 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP362": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/-40576",
        "values": {
            "max_clients": n(256), "ethernet_interfaces": t("1 x 10/100/1000Base-T RJ45"),
            "max_power_consumption_w": n(11.2), "dimensions_mm": t("180 mm diameter x 35 mm depth"),
            "operating_temperature_c": t("-10 to 50 °C"), "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 2 dBi combined; 5 GHz: 5 dBi/chain peak, 3 dBi combined"),
            "wireless_range": t("18 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP371": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1884238220408390169",
        "values": {
            "max_clients": n(256), "ethernet_interfaces": t("1 x 100/1000/2500Base-T RJ45"),
            "power_method": t("IEEE 802.3af/802.3at PoE or 12 V DC"),
            "max_power_consumption_w": n(13.3, "13.3 W excluding USB"),
            "dimensions_mm": t("180 mm diameter x 35 mm depth"), "operating_temperature_c": t("-10 to 50 °C"),
            "antenna_type": t("Built-in smart antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 1 dBi combined; 5 GHz: 5 dBi/chain peak, 3 dBi combined"),
            "wireless_range": t("18 m optimal signal distance"),
            "fast_roaming": t("Seamless roaming with signal steering"), "centralized_management": t(CENTRAL),
        },
    },
    "AP761": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1349309035639238400",
        "values": {
            "max_channel_width_mhz": n(80, "2.4 GHz: 40 MHz; 5 GHz: 80 MHz"),
            "max_clients": n(1024), "ethernet_interfaces": t("1 x 1GbE RJ45; 1 x 1GbE SFP"),
            "power_method": t("IEEE 802.3af/802.3at PoE"), "max_power_consumption_w": n(17.7),
            "dimensions_mm": t("69 x 200 x 200 mm"), "operating_temperature_c": t("-40 to 65 °C"),
            "antenna_type": t("Built-in directional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 11 dBi"),
            "wireless_range": t("180 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
    "AP771": {
        "url": "https://ekit.huawei.com/brand/en/product/sme-network/wlan/1727440602196869358",
        "values": {
            "max_clients": n(256), "ethernet_interfaces": t("1 x 100/1000/2500Base-T RJ45"),
            "power_method": t("IEEE 802.3af/802.3at PoE"), "max_power_consumption_w": n(18.8),
            "dimensions_mm": t("270 x 196 x 51 mm"), "operating_temperature_c": t("-30 to 60 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4 dBi/chain peak, 2 dBi combined; 5 GHz: 7 dBi/chain peak, 4 dBi combined"),
            "wireless_range": t("130 m optimal signal distance"), "centralized_management": t(CENTRAL),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified HUAWEI eKit access-point specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="eKit").first()
        if not brand:
            raise CommandError("Missing brand: eKit")
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
                raise CommandError(f"Missing eKit product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official exact-model product specifications; accessed 2026-10-15",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"HUAWEI eKit {model} product specifications", "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else existing.value_number if existing.value_number is not None else existing.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from the current HUAWEI eKit exact-model product page; management and roaming wording is supported by Huawei eKit's official solution/customer pages.",
                    "verified_date": accessed,
                }
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
                    source_location=f"Official product specifications - {model} - {code}",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
