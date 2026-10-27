from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/fortiap-series.pdf"
SECURITY = "WPA/WPA2/WPA3 with 802.1X or pre-shared key; WEP; captive portal; MAC blocklist/allowlist"
MANAGEMENT = "FortiGate, FortiManagement Cloud, or FortiSASE management"
ROAMING = "IEEE 802.11k/r/v fast roaming"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


PRODUCTS = {
    "FAP-441K": {"page": 4, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "rate_2g_mbps": n(1148), "rate_5g_mbps": n(8648), "rate_6g_mbps": n(11530),
        "total_spatial_streams": n(12, "4x4 service on each of 2.4/5/6 GHz; separate 2x2 scanning radio"),
        "mimo_2g": t("4x4 MU-MIMO"), "mimo_5g": t("4x4 MU-MIMO"), "mimo_6g": t("4x4 MU-MIMO"),
        "max_channel_width_mhz": n(320), "max_clients": n(512, "Up to 512 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("2 x 100M/1G/2.5G/5G/10G multigigabit RJ45; USB 3.0; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE, dual 802.3at PoE, or DC adapter"),
        "max_power_consumption_w": n(41.7), "dimensions_mm": t("250 x 250 x 57.5 mm"),
        "operating_temperature_c": t("0 to 50 °C"), "antenna_type": t("Internal omnidirectional Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 4.0 dBi; 5 GHz: 5.6 dBi; 6 GHz: 5.4 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-241K": {"page": 8, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(4324), "rate_6g_mbps": n(5765),
        "total_spatial_streams": n(6, "2x2 service on each of 2.4/5/6 GHz; separate 2x2 scanning radio"),
        "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"), "mimo_6g": t("2x2 MU-MIMO"),
        "max_channel_width_mhz": n(320), "max_clients": n(512, "Up to 512 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("1 x 100M/1G/2.5G/5G/10G RJ45; 1 x 1GbE RJ45; USB 2.0; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE, IEEE 802.3at PoE with reduced 6 GHz power, or 12 V DC"),
        "max_power_consumption_w": n(26.1), "dimensions_mm": t("190 x 190 x 51 mm"),
        "operating_temperature_c": t("0 to 50 °C"), "antenna_type": t("Internal omnidirectional Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 4.7 dBi; 5 GHz: 5.4 dBi; 6 GHz: 5.7 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-231K": {"page": 12, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(2882), "rate_6g_mbps": n(5765),
        "total_spatial_streams": n(6), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
        "mimo_6g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(320),
        "max_clients": n(256, "Up to 256 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("1 x 100M/1G/2.5G/5G multigigabit RJ45; RS-232 RJ45"),
        "power_method": t("IEEE 802.3at PoE, IEEE 802.3af reduced mode, or 12 V DC"),
        "max_power_consumption_w": n(15.2, "15.2 W PoE input; 14.3 W with 12 V DC"),
        "dimensions_mm": t("175 x 175 x 56 mm"), "operating_temperature_c": t("0 to 50 °C"),
        "antenna_type": t("Internal omnidirectional Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 4.2 dBi; 5 GHz: 5.0 dBi; 6 GHz: 5.1 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-221K": {"page": 16, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(2882), "total_spatial_streams": n(4),
        "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(160),
        "max_clients": n(128, "Up to 128 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("1 x 100M/1G/2.5G RJ45; RS-232 RJ45"),
        "power_method": t("IEEE 802.3at PoE or 12 V DC"), "max_power_consumption_w": n(16.3),
        "dimensions_mm": t("153 x 153 x 50 mm"), "operating_temperature_c": t("0 to 50 °C"),
        "antenna_type": t("Internal dual-band Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 5.7 dBi; 5 GHz: 5.9 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-23JK": {"page": 20, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(2882), "rate_6g_mbps": n(5765),
        "total_spatial_streams": n(6), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
        "mimo_6g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(320),
        "max_clients": n(256, "Up to 256 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("1 x 10GbE multigigabit WAN; 3 x 1GbE LAN; pass-through pair; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE; IEEE 802.3at without PoE-out; 48 V DC"),
        "poe_output": t("LAN3: IEEE 802.3af PoE PSE output"),
        "max_power_consumption_w": n(31, "31 W with PSE out; 19 W without PSE out"),
        "dimensions_mm": t("180 x 120 x 40 mm"), "operating_temperature_c": t("0 to 45 °C"),
        "antenna_type": t("Internal Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 4.0 dBi; 5 GHz: 4.4 dBi; 6 GHz: 3.6 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-244K": {"page": 24, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(4324), "rate_6g_mbps": n(5765),
        "total_spatial_streams": n(6), "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"),
        "mimo_6g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(320),
        "max_clients": n(512, "Up to 512 clients per serving radio"), "max_ssids": n(8),
        "ethernet_interfaces": t("1 x 100M/1G/2.5G/5G RJ45; 1 x 1G/10G SFP+; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE; injector included"), "max_power_consumption_w": n(26),
        "dimensions_mm": t("220 x 220 x 60 mm"), "operating_temperature_c": t("-40 to 70 °C"),
        "ip_rating": t("IP67"), "antenna_type": t("Internal directional Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 8.8 dBi; 5 GHz: 9.4 dBi; 6 GHz: 8.5 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-222KL": {"page": 28, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(688), "rate_5g_mbps": n(4324), "total_spatial_streams": n(4),
        "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(240),
        "max_clients": n(512, "Up to 512 clients per serving radio"), "max_ssids": n(8),
        "ethernet_interfaces": t("1 x 100M/1G/2.5G RJ45 PoE-in; 1 x 10M/100M/1G RJ45 PoE-out; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE; injector included"), "poe_output": t("Port 2: IEEE 802.3af PoE output"),
        "max_power_consumption_w": n(26), "dimensions_mm": t("220 x 220 x 60 mm"),
        "operating_temperature_c": t("-40 to 70 °C"), "ip_rating": t("IP67"),
        "antenna_type": t("External N-type omnidirectional antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 5.0 dBi; 5 GHz: 6.5 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-432FR": {"page": 42, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(1147), "rate_5g_mbps": n(2402), "total_spatial_streams": n(8),
        "mimo_2g": t("4x4 MU-MIMO"), "mimo_5g": t("4x4 MU-MIMO; 2x2 at 160 MHz"),
        "max_channel_width_mhz": n(160), "max_clients": n(512, "Up to 512 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("1 x 2.5GbE RJ45; 1 x 1GbE RJ45 PoE-out; RS-232 RJ45"),
        "power_method": t("IEEE 802.3bt PoE; IEEE 802.3at reduced-power mode"),
        "poe_output": t("1GbE LAN: IEEE 802.3af PoE PSE output when using supplied injector"),
        "max_power_consumption_w": n(37.9, "25 W without PSE out; 37.9 W with PSE out"),
        "dimensions_mm": t("209 x 209 x 60.5 mm"), "operating_temperature_c": t("-40 to 60 °C"),
        "ip_rating": t("IP67"), "antenna_type": t("External N-type dual-band antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 5.5 dBi; 5 GHz: 7.2 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
    "FAP-23JF": {"page": 46, "values": {
        "supported_bands": t("2.4 GHz / 5 GHz"),
        "rate_2g_mbps": n(574), "rate_5g_mbps": n(1200), "total_spatial_streams": n(4),
        "mimo_2g": t("2x2 MU-MIMO"), "mimo_5g": t("2x2 MU-MIMO"), "max_channel_width_mhz": n(80),
        "max_clients": n(512, "Up to 512 clients per serving radio"),
        "max_ssids": n(8, "Up to 8 per client-serving radio; 7 with background scanning"),
        "ethernet_interfaces": t("4 x 1GbE RJ45; pass-through pair; RS-232 RJ45"),
        "power_method": t("IEEE 802.3at PoE, reduced IEEE 802.3af mode, or DC adapter"),
        "poe_output": t("1 x IEEE 802.3af PoE PSE output"),
        "max_power_consumption_w": n(31, "17.5 W without PSE out; 31 W with PSE out"),
        "dimensions_mm": t("168 x 117 x 28 mm"), "operating_temperature_c": t("0 to 50 °C"),
        "antenna_type": t("Internal PCB Wi-Fi antennas"),
        "antenna_gain_dbi": t("2.4 GHz: 4.0 dBi; 5 GHz: 4.0 dBi"),
        "wireless_security": t(SECURITY), "mesh_support": b(True, "Local bridge, Mesh, and Tunnel SSID types"),
        "fast_roaming": t(ROAMING), "centralized_management": t(MANAGEMENT),
    }},
}


class Command(BaseCommand):
    help = "Import manually verified Fortinet FortiAP specifications from the official series datasheet."

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
        document, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL, document_version="Current official FortiAP Series datasheet; accessed 2026-10-15",
            defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                      "title": "Fortinet FortiAP Series Data Sheet", "region": "Global", "published_date": None,
                      "accessed_date": accessed, "active": True},
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
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and
                           (bool((existing.value_text or "").strip()) or existing.value_number is not None or
                            existing.value_boolean is not None))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean)
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                            "value_boolean": None, "normalized_value": str(value), "unit": definition.unit,
                            "raw_value": raw, "source_url": SOURCE_URL[:200],
                            "source_note": f"Manually verified from the official FortiAP Series datasheet, page {item['page']}.",
                            "verified_date": accessed}
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
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
                    source_location=f"p. {item['page']} - FortiAP {model} specifications - {code}",
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
