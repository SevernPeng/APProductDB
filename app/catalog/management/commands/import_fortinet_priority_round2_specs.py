from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


LEGACY_URL = "https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/pt_br/fortiap-series.pdf"
CURRENT_URL = "https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/ja_jp/fortiap-series.pdf"
MATRIX_URL = "https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/Fortinet_Wireless_Product_Matrix.pdf"
SECURITY = "WPA/WPA2/WPA3 with 802.1X or pre-shared key; WEP; captive portal; MAC blocklist/allowlist"
MANAGEMENT = "FortiGate, FortiManagement Cloud, or FortiSASE management"
ROAMING = "IEEE 802.11k/r/v fast roaming"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


COMMON = {
    "wireless_security": t(SECURITY),
    "mesh_support": b(True, "Local-Bridge, Tunnel, and Mesh SSID types"),
    "fast_roaming": t(ROAMING),
    "centralized_management": t(MANAGEMENT),
}


PRODUCTS = {
    "FAP-231F": {
        "url": LEGACY_URL,
        "page": 12,
        "title": "Fortinet FortiAP Series Data Sheet (2021 edition)",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1201),
            "total_spatial_streams": n(4, "2x2 service on 2.4 GHz and 2x2 service on 5 GHz; separate 1x1 scanning radio"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(512, "Up to 512 clients per serving radio"),
            "max_ssids": n(16, "Up to 16; 14 if background scanning is enabled"),
            "ethernet_interfaces": t("2 x 10/100/1000 Base-T RJ45; USB 2.0; RS-232 RJ45 serial"),
            "power_method": t("IEEE 802.3at PoE; IEEE 802.3af reduced mode; optional 12 V DC adapter"),
            "max_power_consumption_w": n(17),
            "dimensions_mm": t("153.2 x 153.2 x 53.0 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("3 internal dual-band Wi-Fi PIFA antennas; internal BLE/Zigbee antenna"),
            "antenna_gain_dbi": t("2.4 GHz: 4.5 dBi; 5 GHz: 5.5 dBi"),
            **COMMON,
        },
    },
    "FAP-431F": {
        "url": LEGACY_URL,
        "page": 6,
        "title": "Fortinet FortiAP Series Data Sheet (2021 edition)",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1147),
            "rate_5g_mbps": n(2402),
            "total_spatial_streams": n(8, "4x4 service on 2.4 GHz and 4x4 service on 5 GHz; separate 1x1 scanning radio"),
            "mimo_2g": t("4x4 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO; 2x2 at 160 MHz"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(512, "Up to 512 clients per serving radio"),
            "max_ssids": n(16, "Up to 16; 14 if background scanning is enabled"),
            "ethernet_interfaces": t("1 x 100M/1G/2.5G Base-T RJ45; 1 x 10/100/1000 Base-T RJ45; USB; RS-232 RJ45 serial"),
            "power_method": t("IEEE 802.3at PoE; dual redundant IEEE 802.3af/at; optional 12 V DC adapter"),
            "max_power_consumption_w": n(24.5),
            "dimensions_mm": t("210 x 210 x 56.5 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
            "antenna_type": t("5 internal PIFA Wi-Fi antennas; internal BLE antenna"),
            "antenna_gain_dbi": t("2.4 GHz: 4.0 dBi; 5 GHz: 5.0 dBi"),
            **COMMON,
        },
    },
    "FAP-234F": {
        "url": CURRENT_URL,
        "page": 48,
        "title": "Fortinet FortiAP Series Data Sheet (current Japanese edition)",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1200),
            "total_spatial_streams": n(4, "2x2 service on 2.4 GHz and 2x2 service on 5 GHz; separate 1x1 scanning radio"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(512, "Up to 512 clients per serving radio"),
            "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
            "ethernet_interfaces": t("2 x 10/100/1000 Base-T RJ45; RS-232 RJ45 serial"),
            "power_method": t("IEEE 802.3at PoE; IEEE 802.3af reduced mode; PoE injector included"),
            "max_power_consumption_w": n(15.5),
            "dimensions_mm": t("316 x 218 x 42 mm"),
            "operating_temperature_c": t("-40 to 60 °C"),
            "ip_rating": t("IP67"),
            "antenna_type": t("Internal directional patch Wi-Fi antennas; internal scanning antenna; BLE/Zigbee antenna"),
            "antenna_gain_dbi": t("Service antennas: 10 dBi at 2.4 and 5 GHz; scanning antenna: 3.5 dBi at 2.4 GHz and 4.5 dBi at 5 GHz"),
            **COMMON,
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified legacy Fortinet FortiAP specifications from official datasheets."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Fortinet").first()
        if not brand:
            raise CommandError("Missing brand: Fortinet")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            url = item["url"]
            if url in documents:
                continue
            documents[url], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version="Official FortiAP datasheet; accessed 2026-10-15",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": item["title"],
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
                raise CommandError(f"Missing Fortinet product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
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
                    "source_note": f"Manually verified from {item['title']}, page {item['page']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"p. {item['page']} - FortiAP {model} specifications - {code}",
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
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
