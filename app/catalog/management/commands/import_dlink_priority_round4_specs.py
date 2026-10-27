from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Supported" if value else "Not supported")


DGS_1016_1024 = "https://www.dlink.com/in/en/-/media/business_products/dgs/dgs-1024d/datasheet/dgs_1016d_1024d_h1_datasheet_en_eu.pdf"
DGS_1008MP = "https://www.dlink.com/en/-/media/business_products/dgs/dgs-1008mp/datasheet/dgs1008mpc1datasheet100hq.pdf"
DSS_16 = "https://support.dlink.com/resource/PRODUCTS/DSS-16PLUS/REVK/DSS-16%2B_REVK_DATASHEET_v2.00_US.pdf"
DPE_301GI = "https://support.dlink.com/resource/products/dpe-301gi/reva/DPE-301GI_REVA_DATASHEET_v1.00_US.pdf"


UNMANAGED_NO_ADVANCED = {
    "loop_prevention": b(False, "No loop prevention function listed for this unmanaged model"),
    "vlan_support": t("Not supported (unmanaged model; no VLAN functions listed)"),
    "link_aggregation": t("Not supported"),
    "igmp_snooping": t("Not supported"),
    "port_mirroring": t("Not supported"),
}


PRODUCTS = {
    "DGS-1016D": {
        "url": DGS_1016_1024,
        "title": "D-Link DGS-1016D/1024D H1 Datasheet",
        "location": "DGS-1016D column and shared specifications, pp. 1-3",
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "port_isolation": b(True, "DIP-switch Port Isolation supported"),
            "qos_support": t("IEEE 802.1p priority with 8 queues"),
            "cable_test": t("Cable diagnostics indicated through port LEDs"),
            "fanless": b(True, "Fanless design; 0 dB(A)"),
            "installation": t("Desktop or wall-mountable; plug-and-play"),
            "max_power_consumption_w": n(10.07),
            "dimensions_mm": t("280 x 125 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DGS-1024D": {
        "url": DGS_1016_1024,
        "title": "D-Link DGS-1016D/1024D H1 Datasheet",
        "location": "DGS-1024D column and shared specifications, pp. 1-3",
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "port_isolation": b(True, "DIP-switch Port Isolation supported"),
            "qos_support": t("IEEE 802.1p priority with 8 queues"),
            "cable_test": t("Cable diagnostics indicated through port LEDs"),
            "fanless": b(True, "Fanless design; 0 dB(A)"),
            "installation": t("Desktop or wall-mountable; plug-and-play"),
            "max_power_consumption_w": n(13.3),
            "dimensions_mm": t("280 x 180 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DGS-1008MP": {
        "url": DGS_1008MP,
        "title": "D-Link DGS-1008MP C1 Datasheet v1.00",
        "location": "Product description and technical specifications, pp. 1-3",
        "values": {
            "extend_mode": b(False, "No extend mode listed for C1"),
            "poe_auto_recovery": b(False, "No PoE auto-recovery function listed for C1"),
            "port_isolation": b(False, "No port isolation function listed for C1"),
            "loop_prevention": b(False, "No loop prevention function listed for C1"),
            "vlan_support": t("Not supported (unmanaged model; no VLAN functions listed)"),
            "qos_support": t("Not supported"),
            "link_aggregation": t("Not supported"),
            "igmp_snooping": t("Not supported"),
            "port_mirroring": t("Not supported"),
            "cable_test": t("Cable diagnostics supported"),
            "installation": t("Desktop or standard 1U rackmount; plug-and-play"),
            "max_power_consumption_w": n(149, "149 W with PoE on; 5.31 W with PoE off"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DSS-16+": {
        "url": DSS_16,
        "title": "D-Link DSS-16+ / DES-1024D K1/G1 Datasheet v2.00",
        "location": "DSS-16+ K1 column and shared specifications, pp. 1-3",
        "values": {
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("Not supported in hardware revision K1 datasheet"),
            "igmp_snooping": t("Not supported"),
            "port_isolation": b(False, "No port isolation function listed for K1"),
            "loop_prevention": b(False, "No loop prevention function listed for K1"),
            "fanless": b(True, "Fanless, quiet design"),
            "installation": t("Desktop or rackmount; plug-and-play"),
            "max_power_consumption_w": n(2.1),
            "dimensions_mm": t("282 x 150 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DPE-301GI": {
        "url": DPE_301GI,
        "title": "D-Link DPE-301GI / DPE-301GS Datasheet v1.00",
        "location": "DPE-301GI technical specifications",
        "values": {
            "accessory_poe_standard": t("IEEE 802.3af / IEEE 802.3at"),
            "accessory_power_w": n(32.4),
            "accessory_data_rate_gbps": n(1, "10/100/1000BASE-T; 1 Gbps maximum"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz"),
            "accessory_output_power": t("54 V ±2 V DC, 600 mA; 32.4 W maximum"),
            "accessory_compatibility": t("IEEE 802.3af/at PoE devices using 10/100/1000BASE-T Ethernet"),
            "dimensions_mm": t("109.8 x 62.2 x 24.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link unmanaged-switch and injector specifications (round 4)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current exact-model document accessed 2026-10-14",
                defaults={
                    "brand": brand,
                    "product": None if model in {"DGS-1016D", "DGS-1024D"} else product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global/official regional support",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the exact model/revision column in the official datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{row['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
