from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def na(raw):
    return "not_applicable", None, raw


PRODUCTS = {
    "TEG-10GBRJ100": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=105_TEG-10GBRJ100",
        "version": "V1, official data sheet dated 2025-10-06",
        "values": {
            "accessory_connector_type": t("RJ-45", "Shielded RJ-45 copper interface"),
            "accessory_interface_type": t("SFP+", "SFP+ MSA compliant; hot-pluggable"),
            "accessory_data_rate_gbps": n(10, "1000BASE-T and 10GBASE-T"),
            "accessory_max_distance_km": n(0.1, "10Gbps up to 100 m with Cat6A/7; 1Gbps up to 100 m with Cat5e"),
            "accessory_compatibility": t("MSA-compliant 10G SFP+ slot; Cat6A/7 for 10Gbps at 100m"),
            "accessory_fiber_mode": na("Copper SFP+ module; fiber mode and wavelength do not apply"),
            "accessory_wavelength_nm": na("Copper SFP+ module; no optical wavelength"),
            "max_power_consumption_w": n(2.5),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("68.5 x 13.8 x 13.8 mm"),
        },
    },
    "TEG-10GBS10": {
        "url": "https://downloads.trendnet.com/TEG-10GBS10_v3/datasheets/EN_datasheet_TEG-10GBS10_%28v3.0R%29.pdf",
        "version": "v3.0R, updated 2021-04-29",
        "values": {
            "accessory_connector_type": t("LC/UPC duplex"),
            "accessory_interface_type": t("SFP+", "SFP+ MSA compliant"),
            "accessory_data_rate_gbps": n(10.31),
            "accessory_input_power": t("Single 3.3 V supply"),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1310),
            "accessory_fiber_mode": t("Single-mode"),
            "accessory_max_distance_km": n(10),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant 10G SFP+ slot; duplex LC single-mode fiber"),
            "max_power_consumption_w": n(0.8),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TEG-10GBS10D2": {
        "url": "https://www.trendnet.com/products/10g-bidi-sfp-plus/10g-sfp-plus-dual-wavelength-single-mode-lc-module-10km-TEG-10GBS10D2-v1",
        "version": "V1, current official product page",
        "values": {
            "fanless": na("Fan design is not a published/applicable transceiver specification"),
            "accessory_connector_type": t("LC simplex"),
            "accessory_interface_type": t("SFP+", "SFP+ MSA compliant"),
            "accessory_data_rate_gbps": n(10.31),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1270, "Transmit 1270 nm / receive 1330 nm"),
            "accessory_fiber_mode": t("Single-mode BiDi/WDM"),
            "accessory_max_distance_km": n(10),
            "accessory_compatibility": t("Must be paired with TEG-10GBS10D3; MSA-compliant 10G SFP+ slot"),
            "accessory_mounting_type": na("Rack mounting does not apply to an SFP+ transceiver"),
            "accessory_rack_units": na("Rack units do not apply to an SFP+ transceiver"),
            "max_power_consumption_w": n(1),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TEG-10GBS10D3": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=105_TEG-10GBS10D3",
        "version": "V1, current official product page",
        "values": {
            "fanless": na("Fan design is not a published/applicable transceiver specification"),
            "accessory_connector_type": t("LC simplex"),
            "accessory_interface_type": t("SFP+", "SFP+ MSA compliant"),
            "accessory_data_rate_gbps": n(10.31),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1330, "Transmit 1330 nm / receive 1270 nm"),
            "accessory_fiber_mode": t("Single-mode BiDi/WDM"),
            "accessory_max_distance_km": n(10),
            "accessory_compatibility": t("Must be paired with TEG-10GBS10D2; MSA-compliant 10G SFP+ slot"),
            "accessory_mounting_type": na("Rack mounting does not apply to an SFP+ transceiver"),
            "accessory_rack_units": na("Rack units do not apply to an SFP+ transceiver"),
            "max_power_consumption_w": n(1),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TEG-10GBSR": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=125_TEG-10GBSR",
        "version": "v2.1R, data sheet dated 2023-03-30",
        "values": {
            "accessory_connector_type": t("LC duplex"),
            "accessory_interface_type": t("SFP+", "SFP+ MSA compliant"),
            "accessory_data_rate_gbps": n(10.5, "Supported throughput 8.5-10.5 Gbps"),
            "accessory_input_power": t("Single 3.3 V supply"),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(850),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(0.3, "300 m OM3; 82 m OM2; 33 m OM1"),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant SFP+ slot; duplex LC multi-mode fiber"),
            "max_power_consumption_w": n(0.439, "Consumption: 439 mW"),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("14.8 x 56.5 x 11.85 mm"),
        },
    },
    "TEG-MGBRJ": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=110_TEG-MGBRJ",
        "version": "v2.0R, current official support page",
        "values": {
            "accessory_connector_type": t("RJ-45"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_fiber_mode": na("Copper SFP module; fiber mode and wavelength do not apply"),
            "accessory_wavelength_nm": na("Copper SFP module; no optical wavelength"),
            "accessory_max_distance_km": n(0.1, "100 m / 328 ft"),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant SFP slot; 1000BASE-T RJ-45"),
            "max_power_consumption_w": n(0.9),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("68 x 13 x 13 mm"),
        },
    },
    "TEG-MGBS10": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=235_TEG-MGBS10",
        "version": "V4, data sheet dated 2021-10-08",
        "values": {
            "accessory_connector_type": t("LC/UPC duplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_wavelength_nm": n(1310),
            "accessory_fiber_mode": t("Single-mode"),
            "accessory_max_distance_km": n(10),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant SFP slot; duplex LC single-mode fiber"),
            "max_power_consumption_w": n(0.8),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("57 x 13 x 12 mm"),
        },
    },
    "TEG-MGBS20D3": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=105_TEG-MGBS20D3",
        "version": "V2, data sheet dated 2021-08-30",
        "values": {
            "accessory_connector_type": t("LC/UPC simplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1310, "Transmit 1310 nm / receive 1550 nm"),
            "accessory_fiber_mode": t("Single-mode BiDi/WDM"),
            "accessory_max_distance_km": n(20),
            "accessory_compatibility": t("Must be paired with TEG-MGBS20D5 or compatible counterpart; MSA-compliant SFP slot"),
            "max_power_consumption_w": n(0.8),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TEG-MGBS20D5": {
        "url": "https://downloads.trendnet.com/TEG-MGBS20D5_v2/datasheets/EN_datasheet_TEG-MGBS20D5_%28v2.0R%29.pdf",
        "version": "V2 / v2.0R",
        "values": {
            "accessory_connector_type": t("LC/UPC simplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1550, "Transmit 1550 nm / receive 1310 nm"),
            "accessory_fiber_mode": t("Single-mode BiDi/WDM"),
            "accessory_max_distance_km": n(20),
            "accessory_compatibility": t("Must be paired with TEG-MGBS20D3 or compatible counterpart; MSA-compliant SFP slot"),
            "max_power_consumption_w": n(0.8),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TEG-MGBSX": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=235_TEG-MGBSX",
        "version": "V4, data sheet dated 2021-07-06",
        "values": {
            "accessory_connector_type": t("LC/UPC duplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_wavelength_nm": n(850),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(0.55),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant SFP slot; duplex LC multi-mode fiber"),
            "max_power_consumption_w": n(0.8),
            "operating_temperature_c": t("0 to 70 °C"),
            "dimensions_mm": t("57 x 13 x 12 mm"),
        },
    },
    "TI-MGBS20": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=105_TI-MGBS20",
        "version": "V1, data sheet dated 2024-07-22",
        "values": {
            "accessory_connector_type": t("LC/UPC duplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_power_w": na("Use max power consumption for an optical transceiver"),
            "accessory_wavelength_nm": n(1310),
            "accessory_fiber_mode": t("Single-mode"),
            "accessory_max_distance_km": n(20),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant industrial SFP slot; duplex LC single-mode fiber"),
            "max_power_consumption_w": n(1),
            "operating_temperature_c": t("-40 to 85 °C"),
            "dimensions_mm": t("58 x 13.4 x 12.6 mm"),
        },
    },
    "TI-MGBSX": {
        "url": "https://www.trendnet.com/langen/support/support-detail.asp?prod=115_TI-MGBSX",
        "version": "v1.1R, data sheet dated 2019-02-12",
        "values": {
            "accessory_connector_type": t("LC/UPC duplex"),
            "accessory_interface_type": t("SFP", "SFP MSA compliant"),
            "accessory_data_rate_gbps": n(1.25),
            "accessory_wavelength_nm": n(850),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(0.55),
            "accessory_compatibility": t("Hot-pluggable in an MSA-compliant industrial SFP slot; duplex LC multi-mode fiber"),
            "max_power_consumption_w": n(1),
            "operating_temperature_c": t("-40 to 85 °C"),
            "dimensions_mm": t("57 x 13 x 8.5 mm"),
        },
    },
    "TFC-GMSC": {
        "url": "https://www.trendnet.com/products/product-detail?prod=110_TFC-GMSC",
        "version": "v2.1R, current official product page",
        "values": {
            "accessory_connector_type": t("1 x RJ-45; 1 x SC multi-mode fiber"),
            "accessory_interface_type": t("1000BASE-T to 100/1000BASE-SX media converter"),
            "accessory_data_rate_gbps": n(1.25, "Optical fiber data rate: 1.25 Gbps"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz, 0.2 A"),
            "accessory_output_power": t("5 V DC, 1 A adapter output"),
            "accessory_power_w": na("Use max power consumption for this powered media converter"),
            "accessory_wavelength_nm": n(850),
            "accessory_fiber_mode": t("Multi-mode"),
            "accessory_max_distance_km": n(2, "Up to 550 m at Gigabit; up to 2 km at Fast Ethernet"),
            "accessory_compatibility": t("Standalone only; not compatible with TFC-1600 chassis"),
            "max_power_consumption_w": n(2.6),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("102 x 75 x 22.6 mm"),
        },
    },
    "TFC-GSFP": {
        "url": "https://www.trendnet.com/langen/support/support-detail.asp?prod=115_TFC-GSFP",
        "version": "v1.2R, current official support page",
        "values": {
            "accessory_connector_type": t("1 x RJ-45; 1 x SFP slot"),
            "accessory_interface_type": t("1000BASE-T to 100/1000BASE-SX/LX SFP media converter"),
            "accessory_data_rate_gbps": n(1),
            "accessory_input_power": t("110-240 V AC, 50/60 Hz"),
            "accessory_output_power": t("5 V DC, 1 A adapter output"),
            "accessory_power_w": na("Use max power consumption for this powered media converter"),
            "accessory_fiber_mode": t("SFP-dependent: multi-mode or single-mode"),
            "accessory_max_distance_km": na("Distance depends on the installed SFP module"),
            "accessory_compatibility": t("Accepts 100/1000 Mbps multimode or single-mode SFP modules; not compatible with TFC-1600"),
            "max_power_consumption_w": n(5),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("75 x 60 x 12 mm"),
        },
    },
    "TPE-113GI": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=155_TPE-113GI",
        "version": "V3, data sheet dated 2017-10-23",
        "values": {
            "accessory_connector_type": t("2 x RJ-45"),
            "accessory_interface_type": t("1 x Gigabit data-in; 1 x Gigabit data-and-power-out"),
            "accessory_data_rate_gbps": n(1, "Gigabit Ethernet, 2000 Mbps full duplex"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz, 0.6 A max; included 54 V DC, 0.4 A adapter"),
            "accessory_output_power": t("IEEE 802.3af PoE, up to 15.4 W; Mode A pins 1/2 (+), 3/6 (-)"),
            "accessory_poe_standard": t("IEEE 802.3af"),
            "accessory_power_w": n(15.4, "PoE output up to 15.4 W"),
            "accessory_compatibility": t("Converts a non-PoE Gigabit port to 802.3af PoE; up to 100 m"),
            "accessory_mounting_type": t("Wall-mountable"),
            "max_power_consumption_w": n(15.4),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("67 x 51 x 25 mm"),
        },
    },
    "TPE-115GI": {
        "url": "https://www.trendnet.com/langru/support/support-detail.asp?prod=190_TPE-115Gi",
        "version": "V3, official data sheet dated 2026-03-06",
        "values": {
            "accessory_connector_type": t("2 x RJ-45"),
            "accessory_interface_type": t("1 x Gigabit data-in; 1 x Gigabit data-and-power-out"),
            "accessory_data_rate_gbps": n(1, "Gigabit Ethernet, 2000 Mbps full duplex"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz, 0.8 A max"),
            "accessory_output_power": t("IEEE 802.3af PoE 15.4 W or 802.3at PoE+ 30 W; Mode A"),
            "accessory_poe_standard": t("IEEE 802.3af / 802.3at"),
            "accessory_power_w": n(30, "PoE+ output up to 30 W"),
            "accessory_compatibility": t("Converts a non-PoE Gigabit port to PoE/PoE+; up to 100 m"),
            "accessory_mounting_type": t("Wall-mountable"),
            "max_power_consumption_w": n(1.03, "Maximum consumption with no powered device connected"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("155 x 57 x 33 mm"),
        },
    },
    "TPE-215GI": {
        "url": "https://downloads.trendnet.com/TPE-215GI/datasheets/EN_intl_datasheet_TPE-215GI_%28v1.0R%29.pdf",
        "version": "v1.0R, updated 2020-06-17; latest detailed official sheet retrievable",
        "values": {
            "accessory_connector_type": t("2 x RJ-45"),
            "accessory_interface_type": t("1 x 2.5GBASE-T data; 1 x 2.5GBASE-T data-and-power-out"),
            "accessory_data_rate_gbps": n(2.5),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz, 1.2 A max"),
            "accessory_output_power": t("IEEE 802.3af PoE 15.4 W or 802.3at PoE+ 30 W"),
            "accessory_poe_standard": t("IEEE 802.3af / 802.3at"),
            "accessory_power_w": n(30, "PoE budget: 30 W max"),
            "accessory_compatibility": t("Converts a non-PoE 2.5GBASE-T port to PoE/PoE+; Cat5e or better; up to 100 m"),
            "accessory_mounting_type": t("Wall-mountable metal enclosure"),
            "max_power_consumption_w": n(0.7, "Maximum consumption without powered device"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("154 x 73 x 36 mm"),
        },
    },
    "TPE-319GI": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=125_TPE-319GI",
        "version": "V2, data sheet dated 2023-06-23",
        "values": {
            "accessory_connector_type": t("2 x RJ-45"),
            "accessory_interface_type": t("1 x 10GBASE-T data; 1 x 10GBASE-T data-and-power-out"),
            "accessory_data_rate_gbps": n(10),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz, 2.0 A max"),
            "accessory_output_power": t("IEEE 802.3af PoE 15.4 W, 802.3at PoE+ 30 W, or 802.3bt PoE++ 90 W"),
            "accessory_poe_standard": t("IEEE 802.3af / 802.3at / 802.3bt"),
            "accessory_power_w": n(90, "PoE budget: 90 W max"),
            "accessory_compatibility": t("10G up to 100 m over Cat6A; backward-compatible 1G over Cat5e; PoE/PoE+/PoE++"),
            "accessory_mounting_type": t("Wall-mountable metal enclosure"),
            "max_power_consumption_w": n(0.7, "Maximum consumption without powered device"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("193 x 82 x 38 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified TRENDnet transceiver, converter, and PoE injector specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="TRENDnet").first()
        if not brand:
            raise CommandError("Missing brand: TRENDnet")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            doc_type = (
                SourceDocument.DocumentType.DATASHEET
                if item["url"].lower().endswith(".pdf")
                else SourceDocument.DocumentType.PRODUCT_PAGE
            )
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=item["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": doc_type,
                    "title": "TRENDnet official accessory specifications",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing TRENDnet product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had_published = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                old_signature = None
                if existing:
                    old_signature = (
                        existing.value_status,
                        existing.value_text,
                        existing.value_number,
                        existing.value_boolean,
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": "" if value is None else str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from current official source ({item['version']}).",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "text":
                    defaults["value_text"] = str(value)
                else:
                    defaults["value_status"] = ProductSpec.ValueStatus.NOT_APPLICABLE
                    defaults["normalized_value"] = "not_applicable"

                new_signature = (
                    defaults["value_status"],
                    defaults["value_text"],
                    defaults["value_number"],
                    defaults["value_boolean"],
                )
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if old_signature is None or (not had_published and kind != "not_applicable"):
                    newly_filled += 1
                    model_new += 1
                elif old_signature != new_signature:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"Specifications - {model} - {code}",
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
                f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
                f"unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
