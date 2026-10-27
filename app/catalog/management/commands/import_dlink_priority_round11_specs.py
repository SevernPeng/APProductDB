from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


SOURCES = {
    "dap3666": {
        "url": "https://support.dlink.com/resource/products/dap-3666/reva/DAP-3666_A1_Datasheet_v1.03(WW).pdf",
        "version": "Datasheet v1.03 (WW), updated 2023-08-04; accessed 2026-10-14",
        "title": "D-Link DAP-3666 Datasheet v1.03",
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "guide": {
        "url": "https://www.dlink.com/bg/bg/-/media/resource-centre/brochures-and-product-guides/nuclias-connect-solution-guide-eu.pdf",
        "version": "Nuclias Connect solution guide, current official copy; accessed 2026-10-14",
        "title": "D-Link Nuclias Connect Solution Guide",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
    "dbax": {
        "url": "https://support.dlink.com/resource/products/DBA-X2830P/REVA/DBA-X1230P%20DBA-X2830P_A1_Datasheet_v1.20(WW).pdf",
        "version": "Datasheet v1.20 (WW); accessed 2026-10-14",
        "title": "D-Link DBA-X1230P / DBA-X2830P Datasheet v1.20",
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "dap2610": {
        "url": "https://support.dlink.com/resource/PRODUCTS/DAP-2610/REVA/DAP-2610_REVA_DATASHEET_1.00_US_EN.pdf",
        "version": "Datasheet v1.00 US, hardware revision A; accessed 2026-10-14",
        "title": "D-Link DAP-2610 Datasheet v1.00",
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "dap2680": {
        "url": "https://support.dlink.com/resource/PRODUCTS/DAP-2680/REVA/DAP-2680_REVA_DATASHEET_v5.00_US.pdf",
        "version": "Datasheet v5.00 US, newest support-directory revision; accessed 2026-10-14",
        "title": "D-Link DAP-2680 Datasheet v5.00",
        "type": SourceDocument.DocumentType.DATASHEET,
    },
}


PRODUCTS = {
    "DAP-3666": {
        "values": {
            "antenna_gain_dbi": (t("2.4 GHz: 6 dBi; 5 GHz: 7 dBi"), "dap3666", "p. 5, Antennas"),
            "antenna_type": (t("4 x internal dual-band antennas"), "dap3666", "p. 5, Antennas"),
            "centralized_management": (t("D-Link Nuclias Connect"), "dap3666", "p. 5, Network Management"),
            "dimensions_mm": (t("277 x 240 x 50 mm"), "dap3666", "p. 5, Dimensions"),
            "ethernet_interfaces": (t("2 x Gigabit LAN (one supports PoE)"), "dap3666", "p. 5, Device Interfaces"),
            "fast_roaming": (t("802.11k/v/r"), "dap3666", "p. 5, Other Features"),
            "ip_rating": (t("IP68"), "dap3666", "p. 5, Certifications"),
            "max_clients": (n(100, "100 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
            "max_power_consumption_w": (n(10.5, "10.5 W"), "dap3666", "p. 5, Maximum Power Consumption"),
            "mimo_2g": (t("2x2 MU-MIMO"), "dap3666", "AC1200 Wave 2 radio and antenna configuration"),
            "mimo_5g": (t("2x2 MU-MIMO"), "dap3666", "AC1200 Wave 2 radio and antenna configuration"),
            "operating_temperature_c": (t("-30 to 60 °C"), "dap3666", "p. 5, Temperature"),
            "power_method": (t("IEEE 802.3af PoE / 54 V DC adapter"), "dap3666", "p. 5, Power Supply"),
            "rate_2g_mbps": (n(300, "Up to 300 Mbps"), "dap3666", "p. 5, Data Signal Rate"),
            "rate_5g_mbps": (n(866, "Up to 866 Mbps"), "dap3666", "p. 5, Data Signal Rate"),
            "total_spatial_streams": (n(4, "2 streams per band; 4 total"), "dap3666", "AC1200 2x2 dual-band configuration"),
            "wireless_security": (t("WPA/WPA2-Personal/Enterprise; WEP 64/128-bit"), "dap3666", "p. 5, Security Features"),
        }
    },
    "DBA-X1230P": {
        "values": {
            "mimo_2g": (t("2x2 MU-MIMO"), "dbax", "Technical specifications, antenna/radio configuration"),
            "mimo_5g": (t("2x2 MU-MIMO"), "dbax", "Technical specifications, antenna/radio configuration"),
            "total_spatial_streams": (n(4, "2 spatial streams per band; 4 total"), "dbax", "Technical specifications"),
        }
    },
    "DBA-X2830P": {
        "values": {
            "mimo_2g": (t("4x4 MU-MIMO"), "dbax", "Technical specifications, antenna/radio configuration"),
            "mimo_5g": (t("4x4 MU-MIMO"), "dbax", "Technical specifications, antenna/radio configuration"),
            "total_spatial_streams": (n(8, "4 spatial streams per band; 8 total"), "dbax", "Technical specifications"),
        }
    },
    "DAP-2610": {
        "values": {
            "max_clients": (n(50, "50 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
            "operating_temperature_c": (t("0 to 40 °C"), "dap2610", "p. 3, Temperature"),
        }
    },
    "DAP-2680": {
        "values": {
            "max_clients": (n(80, "80 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
            "operating_temperature_c": (t("0 to 40 °C"), "dap2680", "p. 5, Temperature"),
        }
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link wireless AP specifications (round 11)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")

        # The source workbook used DBA-3666, but D-Link's product page, support
        # directory, datasheet and order information all identify DAP-3666.
        product = Product.objects.filter(brand=brand, model__in=["DBA-3666", "DAP-3666"]).first()
        if not product:
            raise CommandError("Missing published D-Link product: DBA-3666 / DAP-3666")
        renamed = product.model != "DAP-3666"
        if renamed:
            if product.product_model:
                pm = product.product_model
                pm.model = "DAP-3666"
                pm.model_key = "DAP3666"
                pm.product_name = "Nuclias Connect AC1200 Wave 2 Outdoor Access Point"
                pm.summary = "Outdoor Wi-Fi 5 access point managed by Nuclias Connect."
                pm.save(update_fields=["model", "model_key", "product_name", "summary", "updated_at"])
            product.model = "DAP-3666"
            product.model_key = "DAP3666"
            product.wifi_standard = "Wi-Fi 5"
            product.official_url = "https://www.dlink.com/middle-east/en/products/dap-3666-wireless-ac1200-wave-2-dual-band-outdoor-poe-access-point"
            product.notes = ((product.notes or "") + "\nCorrected model from DBA-3666 to official DAP-3666 nomenclature on 2026-10-14.").strip()
            product.save(update_fields=["model", "model_key", "wifi_standard", "official_url", "notes", "updated_at"])

        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source_documents = {}
        for key, data in SOURCES.items():
            source_documents[key], _ = SourceDocument.objects.update_or_create(
                url=data["url"],
                document_version=data["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": data["type"],
                    "title": data["title"],
                    "region": "Worldwide",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, ((kind, value, raw), source_key, location) in row["values"].items():
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

                source_data = SOURCES[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": source_data["url"][:200],
                    "source_note": "Manually verified from the cited official D-Link product document; newest available document revision was preferred.",
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
                    source_document=source_documents[source_key],
                    source_location=f"{location} - {model}",
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
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} "
            f"models={len(PRODUCTS)} model_renamed={int(renamed)}"
        ))
        self.stdout.write("; ".join(details))
