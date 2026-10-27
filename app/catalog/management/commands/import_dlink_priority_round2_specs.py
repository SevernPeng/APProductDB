from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


DBA_PAGE = "https://www.dlink.com/middle-east/en/products/dba-2520p-nuclias-wireless-ac1900-wave-2-cloud-managed-access-point"
DBA_PDF = "https://support.dlink.com/resource/PRODUCTS/DBA-2520P/REVA/DBA-2520P_REVA_DATASHEET_v1.01_US.pdf"
DAP_X3060W_PDF = "https://www2.dlink.com/en/-/media/product-pages/dap/x3060w/dapx3060wa1datasheetv100ww.pdf"
DAP_X3060W_PAGE = "https://www.dlink.com/es/es/products/dap-x3060w-ax3000-wifi-6-wall-plate-access-point"
DAP_E3620_PDF = "https://www2.dlink.com/en/-/media/product-pages/dap/e3620/dape3620a1datasheetv101ww.pdf"
DAP_E3620_PAGE = "https://www2.dlink.com/en/products/dap-e3620-be3600-wi-fi-7-ceiling-mount-access-point"
DAP_E3620OU_PDF = "https://media.dlink.eu/products/DAP/DAP-E3620OU/DAP-E3620OU_A1_Datasheet_EN_EU.pdf"


PRODUCTS = {
    "DBA-2520P": {
        "sources": [
            (DBA_PDF, SourceDocument.DocumentType.DATASHEET, "D-Link DBA-2520P Datasheet v1.01", "Technical specifications, pp. 5-6"),
            (DBA_PAGE, SourceDocument.DocumentType.PRODUCT_PAGE, "D-Link DBA-2520P Product Page", "Product highlights and specifications"),
        ],
        "values": {
            "total_spatial_streams": (n(3, "Three spatial streams"), 1),
            "rate_2g_mbps": (n(600, "Up to 600 Mbps"), 0),
            "rate_5g_mbps": (n(1299, "Up to 1299 Mbps"), 0),
            "ethernet_interfaces": (t("2 x 10/100/1000 Mbps Ethernet; 1 x RJ45 console"), 0),
            "power_method": (t("IEEE 802.3at PoE on LAN 1 or 12 V DC / 2.5 A adapter"), 0),
            "mimo_2g": (t("3x3 MU-MIMO"), 1),
            "mimo_5g": (t("3x3 MU-MIMO"), 1),
            "antenna_type": (t("Internal omnidirectional antennas"), 0),
            "antenna_gain_dbi": (t("3 dBi at 2.4 GHz; 4 dBi at 5 GHz"), 0),
            "centralized_management": (t("Nuclias Cloud"), 0),
            "fast_roaming": (t("IEEE 802.11k/r roaming"), 1),
            "max_power_consumption_w": (n(19.68, "19.68 W via PoE; 16.92 W via adapter"), 0),
            "dimensions_mm": (t("224.5 x 223.85 x 50 mm"), 0),
            "operating_temperature_c": (t("0 to 40 °C"), 0),
        },
    },
    "DAP-X3060W": {
        "sources": [
            (DAP_X3060W_PDF, SourceDocument.DocumentType.DATASHEET, "D-Link DAP-X3060W Datasheet A1 v1.00", "Technical specifications, p. 2"),
            (DAP_X3060W_PAGE, SourceDocument.DocumentType.PRODUCT_PAGE, "D-Link DAP-X3060W Product Page", "Highlights and technical specifications"),
        ],
        "values": {
            "total_spatial_streams": (n(4, "Dual-band 2x2 MIMO (2x2 + 2x2)"), 1),
            "ethernet_interfaces": (t("1 x Gigabit Ethernet PoE uplink; 3 x Gigabit Ethernet downlink"), 0),
            "poe_output": (t("One Gigabit downlink port provides PoE PSE output"), 0),
            "mimo_2g": (t("2x2 MIMO"), 1),
            "mimo_5g": (t("2x2 MIMO"), 1),
            "max_power_consumption_w": (n(23, "16 W; 23 W including PoE output"), 1),
        },
    },
    "DAP-E3620": {
        "sources": [
            (DAP_E3620_PDF, SourceDocument.DocumentType.DATASHEET, "D-Link DAP-E3620 Datasheet A1 v1.01", "Product highlights and specifications, pp. 1-3"),
            (DAP_E3620_PAGE, SourceDocument.DocumentType.PRODUCT_PAGE, "D-Link DAP-E3620 Product Page", "Education deployment benefits"),
        ],
        "values": {
            "total_spatial_streams": (n(4, "Wi-Fi 7 dual-band 2x2 + 2x2"), 0),
            "mimo_2g": (t("2x2 MIMO"), 0),
            "mimo_5g": (t("2x2 MIMO"), 0),
            "fast_roaming": (t("Fast roaming supported"), 1),
        },
    },
    "DAP-E3620OU": {
        "sources": [
            (DAP_E3620OU_PDF, SourceDocument.DocumentType.DATASHEET, "D-Link DAP-E3620OU Datasheet A1 v1.00 EU", "Product highlights and specifications, pp. 1-3"),
        ],
        "values": {
            "total_spatial_streams": (n(4, "Wi-Fi 7 dual-band 2x2 + 2x2"), 0),
        },
    },
}


CLEAR_INVALID = {
    "DAP-X3060": {"wireless_range": "Scraped disclaimer fragment, not a range specification"},
    "DAP-E3620": {
        "max_ssids": "Model number was misparsed as an SSID count",
        "wireless_range": "Scraped disclaimer fragment, not a range specification",
    },
    "DAP-E3620OU": {"max_ssids": "Model number was misparsed as an SSID count"},
}


class Command(BaseCommand):
    help = "Import manually verified D-Link access-point specifications (round 2)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        codes.update(code for values in CLEAR_INVALID.values() for code in values)
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = cleared = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            sources = []
            for url, document_type, title, location in row["sources"]:
                source, _ = SourceDocument.objects.update_or_create(
                    url=url,
                    document_version="Current official document accessed 2026-10-14",
                    defaults={
                        "brand": brand,
                        "product": product,
                        "document_type": document_type,
                        "title": title,
                        "region": "Global/official regional site",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
                sources.append((source, location))

            model_new = model_corrected = 0
            for code, ((kind, value, raw), source_index) in row["values"].items():
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
                source, location = sources[source_index]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": source.url[:200],
                    "source_note": "Manually verified from the official exact-model product page or datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
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
                    source_location=f"{location} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        for model, values in CLEAR_INVALID.items():
            product = Product.objects.get(brand=brand, model=model, is_published=True)
            for code, reason in values.items():
                spec, _ = ProductSpec.objects.get_or_create(product=product, definition=definitions[code])
                has_any = bool((spec.value_text or "").strip()) or spec.value_number is not None or spec.value_boolean is not None
                if has_any or spec.value_status == ProductSpec.ValueStatus.PUBLISHED:
                    spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                    spec.value_text = ""
                    spec.value_number = None
                    spec.value_boolean = None
                    spec.normalized_value = ""
                    spec.raw_value = ""
                    spec.source_url = ""
                    spec.source_note = reason
                    spec.verified_date = accessed
                    spec.save()
                    cleared += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} cleared_invalid={cleared} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
