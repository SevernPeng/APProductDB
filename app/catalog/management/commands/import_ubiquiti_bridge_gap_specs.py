from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "UBB": (
        "https://techspecs.ui.com/unifi/wifi/ubb?s=us",
        "Ubiquiti UniFi Building Bridge official Tech Specs",
    ),
    "UBB_XG": (
        "https://techspecs.ui.com/unifi/wifi/ubb-xg?subcategory=all-wifi",
        "Ubiquiti UniFi Building Bridge XG official Tech Specs",
    ),
    "UDB_PRO": (
        "https://techspecs.ui.com/unifi/wifi/udb-pro?subcategory=all-wifi",
        "Ubiquiti UniFi Device Bridge Pro official Tech Specs",
    ),
    "UDB_PRO_SECTOR": (
        "https://techspecs.ui.com/unifi/wifi/udb-pro-sector?s=us",
        "Ubiquiti UniFi Device Bridge Pro Sector official Tech Specs",
    ),
    "LBE": (
        "https://techspecs.ui.com/uisp/wireless/litebeam-5ac?subcategory=all-wireless",
        "Ubiquiti UISP airMAX LiteBeam 5AC official Tech Specs",
    ),
    "LBE_DS": (
        "https://dl.ui.com/datasheets/LiteBeam/LiteBeam_AC_Gen2_DS.pdf",
        "Ubiquiti LiteBeam AC Gen2 Datasheet",
    ),
    "WAVE_MLO6": (
        "https://techspecs.ui.com/uisp/wireless/wave-mlo6?subcategory=all-wireless",
        "Ubiquiti UISP Wave MLO6 official Tech Specs",
    ),
}

ITEMS = []


def add(models, code, kind, value, raw, source, location):
    for model in models:
        ITEMS.append({
            "model": model,
            "code": code,
            "kind": kind,
            "value": value,
            "raw": raw,
            "source": source,
            "location": location,
        })


# UniFi Building Bridge (UBB).
add(("Building Bridge",), "antenna_gain_dbi", "text", "17.2 dBi at 60 GHz; 10 dBi at 5 GHz; 2 dBi at 2.4 GHz BLE", "Antenna gain: 60 GHz 17.2 dBi; 5 GHz 10 dBi; 2.4 GHz 2 dBi (BLE)", "UBB", "Performance — Antenna Gain")
add(("Building Bridge",), "dimensions_mm", "text", "140 x 90 mm", "Dimensions: diameter 140 x 90 mm", "UBB", "Overview — Dimensions")
add(("Building Bridge",), "ethernet_interfaces", "text", "1 x GbE RJ45", "Networking interface: (1) GbE RJ45 port", "UBB", "Hardware — Networking Interface")
add(("Building Bridge",), "ip_rating", "text", "IPX6", "Weatherproofing: IPX6", "UBB", "Overview — Weatherproofing")
add(("Building Bridge",), "max_channel_width_mhz", "number", 2160, "Main radio (60 GHz): 1,080/2,160 MHz; backup radio (5 GHz): 20/40/80 MHz", "UBB", "Hardware — Channel Bandwidth")
add(("Building Bridge",), "max_power_consumption_w", "number", 11, "Max. power consumption: 11W", "UBB", "Hardware — Max. Power Consumption")
add(("Building Bridge",), "poe_input", "text", "PoE; 44–57 V DC", "Power method: PoE; supported voltage range: 44–57V DC", "UBB", "Overview / Hardware — Power")
add(("Building Bridge",), "power_method", "text", "PoE", "Power method: PoE", "UBB", "Overview — Power Method")
add(("Building Bridge",), "rate_5g_mbps", "number", 866.6, "Max. data rate, 5 GHz: 866.6 Mbps (BW80)", "UBB", "Performance — Max. Data Rate")
add(("Building Bridge",), "operating_temperature_c", "text", "-40 to 70 °C", "Ambient operating temperature: -40 to 70° C", "UBB", "Hardware — Environment")
add(("Building Bridge",), "wireless_range", "text", "500 m", "Coverage area: 500 m (1,640 ft)", "UBB", "Overview — Coverage Area")
add(("Building Bridge",), "wireless_security", "text", "WPA2 AES", "Wireless security: WPA2 AES", "UBB", "Performance — Wireless Security")
add(("Building Bridge",), "bridge_modes", "text", "Point-to-point (PtP)", "Operating modes: PtP", "UBB", "Hardware — Operating Modes")


# UniFi Building Bridge XG; the database also retains the ordering-code alias UBB-XG.
UBB_XG_MODELS = ("Building Bridge XG", "UBB-XG")
add(UBB_XG_MODELS, "antenna_gain_dbi", "text", "21 dBi at 60 GHz; 14 dBi at 5 GHz; 2 dBi at 2.4 GHz BLE", "Antenna gain: 60 GHz 21 dBi; 5 GHz 14 dBi; 2.4 GHz 2 dBi (BLE)", "UBB_XG", "Performance — Antenna Gain")
add(UBB_XG_MODELS, "dimensions_mm", "text", "191.8 x 59 mm", "Dimensions: diameter 191.8 x 59 mm", "UBB_XG", "Overview — Dimensions")
add(UBB_XG_MODELS, "ethernet_interfaces", "text", "1 x GbE RJ45; 1 x 1/10G SFP+", "Networking interface: (1) GbE RJ45 port; (1) 1/10G SFP+ port", "UBB_XG", "Hardware — Networking Interface")
add(UBB_XG_MODELS, "ip_rating", "text", "IPX6", "Weatherproofing: IPX6", "UBB_XG", "Overview — Weatherproofing")
add(UBB_XG_MODELS, "max_channel_width_mhz", "number", 4320, "Main radio (60 GHz): 2160/4320 MHz; backup radio (5 GHz): 20/40/80 MHz", "UBB_XG", "Hardware — Channel Bandwidth")
add(UBB_XG_MODELS, "max_power_consumption_w", "number", 29, "Max. power consumption: 29W", "UBB_XG", "Hardware — Max. Power Consumption")
add(UBB_XG_MODELS, "poe_input", "text", "PoE++ or passive PoE; 48 V DC ±10%", "Power method: PoE++, passive PoE; supported voltage range: 48V DC ±10%", "UBB_XG", "Overview / Hardware — Power")
add(UBB_XG_MODELS, "power_method", "text", "PoE++ / passive PoE", "Power method: PoE++ / Passive PoE", "UBB_XG", "Overview — Power Method")
add(UBB_XG_MODELS, "rate_5g_mbps", "number", 866.6, "Max. data rate, 5 GHz: 866.6 Mbps (BW80)", "UBB_XG", "Performance — Max. Data Rate")
add(UBB_XG_MODELS, "operating_temperature_c", "text", "-40 to 55 °C", "Ambient operating temperature: -40 to 55° C", "UBB_XG", "Hardware — Environment")
add(UBB_XG_MODELS, "wireless_range", "text", "500 m", "Coverage area: 500 m (1,640 ft)", "UBB_XG", "Overview — Coverage Area")
add(UBB_XG_MODELS, "wireless_security", "text", "WPA2 AES", "Wireless security: WPA2 AES", "UBB_XG", "Performance — Wireless Security")
add(UBB_XG_MODELS, "bridge_modes", "text", "Point-to-point (PtP)", "Operating modes: PtP", "UBB_XG", "Hardware — Operating Modes")


# UniFi Device Bridge Pro and its model-code alias.
UDB_PRO_MODELS = ("Device Bridge Pro", "UDB-Pro")
add(UDB_PRO_MODELS, "antenna_gain_dbi", "text", "19 dBi at 5 GHz", "Antenna gain, 5 GHz: 19 dBi", "UDB_PRO", "Performance — Antenna Gain")
add(UDB_PRO_MODELS, "antenna_type", "text", "Internal", "Antennas: Internal", "UDB_PRO", "Hardware — Antennas")
add(UDB_PRO_MODELS, "dimensions_mm", "text", "189.5 x 64.3 mm", "Dimensions: diameter 189.5 x 64.3 mm", "UDB_PRO", "Overview — Dimensions")
add(UDB_PRO_MODELS, "ethernet_interfaces", "text", "2 x GbE RJ45", "Networking interface: (2) GbE RJ45 ports", "UDB_PRO", "Hardware — Networking Interface")
add(UDB_PRO_MODELS, "ip_rating", "text", "IPX6", "Weatherproofing: IPX6", "UDB_PRO", "Overview — Weatherproofing")
add(UDB_PRO_MODELS, "max_channel_width_mhz", "number", 80, "Channel bandwidth: 20/40/80 MHz", "UDB_PRO", "Hardware — Channel Bandwidth")
add(UDB_PRO_MODELS, "max_power_consumption_w", "number", 9, "Max. power consumption: 9W", "UDB_PRO", "Hardware — Max. Power Consumption")
add(UDB_PRO_MODELS, "poe_input", "text", "PoE; PoE+ required for PoE output; 42.5–57 V DC", "Power method: PoE; PoE+ required for PoE output; supported voltage range 42.5–57V DC", "UDB_PRO", "Overview / Hardware — Power")
add(UDB_PRO_MODELS, "power_method", "text", "PoE / PoE+", "Power method: PoE; PoE+ required for PoE output", "UDB_PRO", "Overview — Power Method")
add(UDB_PRO_MODELS, "rate_5g_mbps", "number", 867, "Max. data rate, 5 GHz: 867 Mbps (BW80)", "UDB_PRO", "Performance — Max. Data Rate")
add(UDB_PRO_MODELS, "operating_temperature_c", "text", "-40 to 60 °C", "Ambient operating temperature: -40 to 60° C", "UDB_PRO", "Hardware — Environment")
add(UDB_PRO_MODELS, "wireless_range", "text", "5 km", "Coverage area: 5 km (3.1 mi)", "UDB_PRO", "Overview — Coverage Area")
add(UDB_PRO_MODELS, "wireless_security", "text", "WPA2 AES", "Wireless security: WPA2 AES", "UDB_PRO", "Performance — Wireless Security")
add(UDB_PRO_MODELS, "supported_bands", "text", "5 GHz", "WiFi standard: WiFi 5; 5 GHz radio", "UDB_PRO", "Overview / Performance")


# UniFi Device Bridge Pro Sector and its model-code alias.
UDB_SECTOR_MODELS = ("Device Bridge Pro Sector", "UDB-Pro-Sector")
add(UDB_SECTOR_MODELS, "antenna_gain_dbi", "text", "17 dBi at 5 GHz", "Antenna gain, 5 GHz: 17 dBi", "UDB_PRO_SECTOR", "Performance — Antenna Gain")
add(UDB_SECTOR_MODELS, "antenna_type", "text", "Internal", "Antennas: Internal", "UDB_PRO_SECTOR", "Hardware — Antennas")
add(UDB_SECTOR_MODELS, "dimensions_mm", "text", "360.9 x 129.6 x 71.4 mm", "Dimensions: 360.9 x 129.6 x 71.4 mm", "UDB_PRO_SECTOR", "Overview — Dimensions")
add(UDB_SECTOR_MODELS, "ethernet_interfaces", "text", "1 x GbE RJ45", "Networking interface: (1) GbE RJ45 port", "UDB_PRO_SECTOR", "Hardware — Networking Interface")
add(UDB_SECTOR_MODELS, "ip_rating", "text", "IPX6", "Weatherproofing: IPX6", "UDB_PRO_SECTOR", "Overview — Weatherproofing")
add(UDB_SECTOR_MODELS, "max_channel_width_mhz", "number", 40, "Channel bandwidth: 20/40 MHz", "UDB_PRO_SECTOR", "Hardware — Channel Bandwidth")
add(UDB_SECTOR_MODELS, "max_power_consumption_w", "number", 6, "Max. power consumption: 6W", "UDB_PRO_SECTOR", "Hardware — Max. Power Consumption")
add(UDB_SECTOR_MODELS, "poe_input", "text", "PoE; 42.5–57 V DC", "Power method: PoE; supported voltage range 42.5–57V DC", "UDB_PRO_SECTOR", "Overview / Hardware — Power")
add(UDB_SECTOR_MODELS, "power_method", "text", "PoE", "Power method: PoE", "UDB_PRO_SECTOR", "Overview — Power Method")
add(UDB_SECTOR_MODELS, "rate_5g_mbps", "number", 400, "Max. data rate, 5 GHz: 400 Mbps (BW40)", "UDB_PRO_SECTOR", "Performance — Max. Data Rate")
add(UDB_SECTOR_MODELS, "operating_temperature_c", "text", "-40 to 60 °C", "Ambient operating temperature: -40 to 60° C", "UDB_PRO_SECTOR", "Hardware — Environment")
add(UDB_SECTOR_MODELS, "wireless_range", "text", "5 km", "Coverage area: 5 km (3.1 mi)", "UDB_PRO_SECTOR", "Overview — Coverage Area")
add(UDB_SECTOR_MODELS, "wireless_security", "text", "WPA2 AES", "Wireless security: WPA2 AES", "UDB_PRO_SECTOR", "Performance — Wireless Security")
add(UDB_SECTOR_MODELS, "supported_bands", "text", "5 GHz", "WiFi standard: WiFi 5; 5 GHz radio", "UDB_PRO_SECTOR", "Overview / Performance")


# UISP airMAX LiteBeam 5AC Gen2 is represented by two display-name variants.
LBE_MODELS = ("LBE-5AC-GEN2", "airMAX LBE-5AC-GEN2")
add(LBE_MODELS, "antenna_gain_dbi", "text", "23 dBi at 5 GHz", "Antenna gain: 23 dBi", "LBE", "System — Antenna Gain")
add(LBE_MODELS, "antenna_type", "text", "Integrated directional reflector/feedhorn antenna", "InnerFeed technology integrates the radio into the feedhorn of the antenna; directional reflector design", "LBE_DS", "Overview — Innovative Design")
add(LBE_MODELS, "bridge_modes", "text", "Access Point; Station; bridging; routing", "Operating modes: Access Point, Station; Services: Bridging, Routing", "LBE", "Software — Operating Modes and Services")
add(LBE_MODELS, "dimensions_mm", "text", "358 x 271.95 x 272.5 mm", "Dimensions: 358 x 271.95 x 272.5 mm", "LBE", "Mechanical — Dimensions")
add(LBE_MODELS, "ethernet_interfaces", "text", "1 x GbE RJ45", "Networking interface: (1) GbE RJ45 port", "LBE", "Hardware — Networking Interface")
add(LBE_MODELS, "lightning_protection_kv", "text", "±24 kV contact/air ESD/EMP", "ESD/EMP protection: ±24 kV contact / air", "LBE_DS", "Specifications — ESD/EMP Protection")
add(LBE_MODELS, "max_channel_width_mhz", "number", 80, "PtP channel sizes: 10/20/30/40/50/60/80 MHz; PtMP: 10/20/30/40 MHz", "LBE_DS", "Software — Selectable Channel Width")
add(LBE_MODELS, "max_power_consumption_w", "number", 7, "Max. power consumption: 7W", "LBE", "Hardware — Max. Power Consumption")
add(LBE_MODELS, "poe_input", "text", "24 V passive PoE; 22–27 V DC", "Power method: Passive PoE 2-pair; supported voltage range: 22–27V DC", "LBE", "Hardware — Power")
add(LBE_MODELS, "power_method", "text", "24 V passive PoE", "Power method: Passive PoE 2-pair", "LBE", "Hardware — Power Method")
add(LBE_MODELS, "rate_5g_mbps", "number", 450, "Total throughput: 450+ Mbps", "LBE", "System — Total Throughput")
add(LBE_MODELS, "operating_temperature_c", "text", "-40 to 70 °C", "Ambient operating temperature: -40 to 70° C", "LBE", "Hardware — Environment")
add(LBE_MODELS, "supported_bands", "text", "5 GHz", "Supported frequency range: 5150–5875 MHz", "LBE", "Radio Frequency")
add(LBE_MODELS, "wireless_security", "text", "WPA2", "Strongest WPA2 security", "LBE_DS", "Software — Wireless Features")


# UISP Wave MLO6 publishes combined throughput rather than per-radio PHY rates, so rate fields remain unset.
add(("Wave MLO6",), "antenna_type", "text", "External antennas via 2 x waterproof RP-SMA", "RF connections: (2) RP-SMA (waterproof); (1) GPS (waterproof)", "WAVE_MLO6", "Hardware — RF Connections")
add(("Wave MLO6",), "bridge_modes", "text", "Point-to-point (PtP); bridge mode", "Operating modes: PtP; Network: Bridge Mode", "WAVE_MLO6", "Software — Operating Modes / Network")
add(("Wave MLO6",), "dimensions_mm", "text", "249.3 x 82 x 47.6 mm", "Dimensions: 249.3 x 82 x 47.6 mm", "WAVE_MLO6", "Mechanical — Dimensions")
add(("Wave MLO6",), "ethernet_interfaces", "text", "1 x 10GbE RJ45; 1 x 10G SFP+", "Networking interface: (1) 10 GbE RJ45 port; (1) 10G SFP+ port", "WAVE_MLO6", "Hardware — Networking Interface")
add(("Wave MLO6",), "ip_rating", "text", "IPX6", "Weatherproofing: IPX6", "WAVE_MLO6", "Mechanical — Weatherproofing")
add(("Wave MLO6",), "max_channel_width_mhz", "number", 320, "Radio 1: 20/40/80/160/240 MHz; Radio 2: 20/40/80/160/320 MHz", "WAVE_MLO6", "Radio Frequency — Channel Bandwidth")
add(("Wave MLO6",), "max_power_consumption_w", "number", 20, "Max. power consumption: 20W", "WAVE_MLO6", "Hardware — Max. Power Consumption")
add(("Wave MLO6",), "poe_input", "text", "Passive PoE; 22–27 V or 44–54 V DC", "Power method: passive PoE 4-pairs or passive PoE 2-pairs; supported voltage range 44–54V DC or 22–27V DC", "WAVE_MLO6", "Hardware — Power")
add(("Wave MLO6",), "power_method", "text", "Passive PoE", "Power method: Passive PoE", "WAVE_MLO6", "Hardware — Power Method")
add(("Wave MLO6",), "operating_temperature_c", "text", "-40 to 60 °C", "Ambient operating temperature: -40 to 60° C", "WAVE_MLO6", "Hardware — Environment")
add(("Wave MLO6",), "supported_bands", "text", "5 GHz / 6 GHz", "Operating frequency: 5 GHz and 6 GHz", "WAVE_MLO6", "Radio Frequency — Operating Frequency")
add(("Wave MLO6",), "wireless_range", "text", "100 km", "Max. range: 100 km (62.1 mi)", "WAVE_MLO6", "System — Max. Range")
add(("Wave MLO6",), "wireless_security", "text", "WPA3-PSK (AES)", "Encryption: WPA3-PSK (AES)", "WAVE_MLO6", "System — Encryption")


class Command(BaseCommand):
    help = "Import manually verified Ubiquiti wireless-bridge gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        codes = {item["code"] for item in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for item in ITEMS:
            url, title = SOURCES[item["source"]]
            if url not in documents:
                documents[url], _ = SourceDocument.objects.update_or_create(
                    url=url,
                    document_version="Current official Ubiquiti documentation; accessed 2026-10-20",
                    defaults={
                        "brand": brand,
                        "product": None,
                        "document_type": SourceDocument.DocumentType.SPECIFICATION,
                        "title": title,
                        "region": "Global",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {item['model']}")
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip())
                or existing.value_number is not None
                or existing.value_boolean is not None
            ))
            if item["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(item["value"]))
            elif item["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(item["value"])
            else:
                old_value = existing.value_text if had else None
                new_value = str(item["value"])

            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(item["value"]),
                "unit": definition.unit,
                "raw_value": item["raw"],
                "source_url": url[:200],
                "source_note": "Manually verified from official Ubiquiti Tech Specs or datasheet.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
            elif item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults=defaults,
            )
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=documents[url],
                source_location=item["location"],
                defaults={
                    "source_excerpt": item["raw"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} "
            f"corrected={corrected} unchanged={unchanged}"
        ))
