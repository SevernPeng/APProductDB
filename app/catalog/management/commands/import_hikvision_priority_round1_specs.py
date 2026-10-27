from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


SEC_WPA2 = "WPA2-PSK; WPA/WPA2-PSK; blocklist/allowlist; 802.11i; SSID/VLAN binding"
SEC_WPA3 = "WPA2-PSK; WPA/WPA2-PSK; WPA3-PSK; WPA2/WPA3-PSK; blocklist/allowlist; 802.11i; SSID/VLAN binding"
CENTRAL_EI = "Cloud service and app management; web/SSH; CAPWAP with DTLS encryption"
CENTRAL_SI = "Centralized AC management; web-based upgrade and maintenance"


PRODUCTS = {
    "DS-3WAP5112-EI": {
        "url": "https://pro-av.hikvision.com/mena-en/products/transmission/wireless-access-point/wall-mount-ap/ds-3wap5112-ei/",
        "kind": "page",
        "values": {
            "rate_2g_mbps": n(300), "rate_5g_mbps": n(867),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz up to 40 MHz; 5 GHz up to 80 MHz"),
            "max_clients": n(128), "max_ssids": n(7),
            "ethernet_interfaces": t("1 x 1GbE PoE-in; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3af/at PoE"), "max_power_consumption_w": n(9.5),
            "dimensions_mm": t("86 x 86 x 29.9 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("2 x built-in omnidirectional antennas per band"),
            "antenna_gain_dbi": t("2.4 GHz: 3.1 dBi; 5 GHz: 3.1 dBi"),
            "wireless_range": t("Recommended 40 m²; 15 m radius in open environment"),
            "wireless_security": t("WPA2-PSK; WPA/WPA2-PSK"),
            "fast_roaming": t("802.11k/v roaming; roaming-sensitivity adjustment"),
            "centralized_management": t(CENTRAL_EI),
        },
    },
    "DS-3WAP521-SI": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000013540/S000013559/OFR035719/M000113055/Data_Sheet/DS-3WAP521-SI_Datasheet_20240201-pdf.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(300), "rate_5g_mbps": n(867),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz up to 40 MHz; 5 GHz up to 80 MHz"),
            "max_clients": n(128), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3af/at PoE"), "max_power_consumption_w": n(8),
            "dimensions_mm": t("86 x 86 x 35 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 3 dBi"),
            "wireless_security": t(SEC_WPA2), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
    "DS-3WAP522-SI": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000013540/S000013559/OFR021775/M000113052/Data_Sheet/DS-3WAP522-SI_Datasheet_20240201-pdf.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(300), "rate_5g_mbps": n(867),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz up to 40 MHz; 5 GHz up to 80 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink"),
            "power_method": t("IEEE 802.3af/at PoE or 12 V DC"), "max_power_consumption_w": n(11.35),
            "dimensions_mm": t("220 x 220 x 35 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 4 dBi"),
            "wireless_security": t(SEC_WPA2), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
    "DS-3WAP5312-EI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000171512/DS-3WAP5312-EI_Datasheet_20260228.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(300), "rate_5g_mbps": n(867),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz up to 40 MHz; 5 GHz up to 80 MHz"),
            "max_clients": n(128), "max_ssids": n(7),
            "ethernet_interfaces": t("1 x 1GbE PoE-in; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3at PoE"), "max_power_consumption_w": n(15),
            "dimensions_mm": t("65 x 225 x 32 mm"), "operating_temperature_c": t("-30 to 65 °C"),
            "ip_rating": t("IP65"), "antenna_type": t("External dual-band omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.7 dBi; 5 GHz: 5 dBi"),
            "wireless_range": t("Recommended coverage radius: 150 m"),
            "wireless_security": t("WPA2-PSK; WPA/WPA2-PSK"),
            "fast_roaming": t("Wireless roaming with roaming-sensitivity adjustment"),
            "centralized_management": t(CENTRAL_EI),
        },
    },
    "DS-3WAP6130-EI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000177243/DS-3WAP6130-EI_Datasheet_20260228.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(574), "rate_5g_mbps": n(2402),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(160, "2.4 GHz up to 40 MHz; 5 GHz up to 160 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3af/at PoE"), "max_power_consumption_w": n(13),
            "dimensions_mm": t("86 x 86 x 40.6 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 2.4 dBi; 5 GHz: 2.5 dBi"),
            "wireless_range": t("Recommended 40 m²; 15 m radius in open environment"),
            "wireless_security": t("WPA2-PSK; WPA/WPA2-PSK; WPA3-PSK; WPA2/WPA3-PSK"),
            "fast_roaming": t("Seamless roaming; roaming-sensitivity adjustment"),
            "centralized_management": t(CENTRAL_EI),
        },
    },
    "DS-3WAP621E-SI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000113056/DS-3WAP621E-SI_Datasheet_20240401-1.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(575), "rate_5g_mbps": n(2400),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(160, "2.4 GHz up to 40 MHz; 5 GHz up to 160 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3af/at PoE"), "max_power_consumption_w": n(13),
            "dimensions_mm": t("86 x 86 x 44.4 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 5 dBi"),
            "wireless_security": t(SEC_WPA3), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
    "DS-3WAP622E-SI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000113054/DS-3WAP622E-SI_Datasheet_20240401.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(575), "rate_5g_mbps": n(2400),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(160, "2.4 GHz up to 40 MHz; 5 GHz up to 160 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink"),
            "power_method": t("IEEE 802.3af/at PoE; 12 V DC"), "max_power_consumption_w": n(13.5),
            "dimensions_mm": t("220 x 220 x 39 mm"), "operating_temperature_c": t("0 to 45 °C"),
            "wireless_security": t(SEC_WPA3), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
    "DS-3WAP622G-SI": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000013540/S000013559/OFR021775/M000113053/Data_Sheet/DS-3WAP622G-SI_Datasheet_20240201-pdf.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(574), "rate_5g_mbps": n(1201),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "2.4 GHz up to 40 MHz; 5 GHz up to 80 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink"),
            "power_method": t("IEEE 802.3af/at PoE; 12 V DC"), "max_power_consumption_w": n(11.35),
            "dimensions_mm": t("220 x 220 x 35 mm"), "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3 dBi; 5 GHz: 4 dBi"),
            "wireless_security": t(SEC_WPA3), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
    "DS-3WAP6230-EI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000166836/DS-3WAP6230-EI_Datasheet_20260228.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(574), "rate_5g_mbps": n(2402),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(160, "2.4 GHz up to 40 MHz; 5 GHz up to 160 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in; 1 x 1GbE RJ45"),
            "power_method": t("IEEE 802.3at PoE or 12 V DC"), "max_power_consumption_w": n(18),
            "dimensions_mm": t("220 mm diameter x 49.7 mm depth, excluding bracket"),
            "operating_temperature_c": t("0 to 40 °C"), "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.5 dBi; 5 GHz: 4.5 dBi"),
            "wireless_range": t("Recommended 140 m²; 25 m radius in open environment"),
            "wireless_security": t("WPA2-PSK; WPA/WPA2-PSK; WPA3-PSK; WPA2/WPA3-PSK"),
            "fast_roaming": t("Wireless roaming with roaming-sensitivity adjustment"),
            "centralized_management": t(CENTRAL_EI),
        },
    },
    "DS-3WAP623E-SI": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000113057/DS-3WAP623E-SI_Datasheet_20250925.pdf",
        "kind": "datasheet",
        "values": {
            "rate_2g_mbps": n(575), "rate_5g_mbps": n(2400),
            "total_spatial_streams": n(4), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(160, "2.4 GHz up to 40 MHz; 5 GHz up to 160 MHz"),
            "max_clients": n(256), "max_ssids": n(8),
            "ethernet_interfaces": t("1 x 1GbE PoE-in uplink"),
            "power_method": t("IEEE 802.3af/at PoE; 48 V DC"), "max_power_consumption_w": n(14.4),
            "dimensions_mm": t("102 x 110 x 250 mm"), "operating_temperature_c": t("-30 to 55 °C"),
            "ip_rating": t("IP68"), "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 10 dBi; 5 GHz: 5 dBi"),
            "wireless_security": t(SEC_WPA2), "fast_roaming": t("Intelligent fast roaming"),
            "centralized_management": t(CENTRAL_SI),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Hikvision access-point specifications (round 1)."

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
                document_version="Current official exact-model source; accessed 2026-10-15",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET if item["kind"] == "datasheet" else SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Hikvision {model} official specifications",
                    "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
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
                    "source_note": "Manually verified from Hikvision's current exact-model official product page or datasheet.",
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
                    source_location=f"Official specification table - {model} - {code}",
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
