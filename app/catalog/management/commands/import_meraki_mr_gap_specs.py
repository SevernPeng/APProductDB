from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MODELS = ("MR28", "MR30H", "MR33", "MR36", "MR36H", "MR42", "MR44", "MR46", "MR70", "MR76", "MR78", "MR86")

URLS = {
    "FAQ": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR_Access_Point_FAQ",
    "MESH": "https://documentation.meraki.com/Wireless/Design_and_Configure/Deployment_Guides/Mesh_Deployment_Guide",
    "ROAM": "https://documentation.meraki.com/Platform_Management/Dashboard_Administration/Design_and_Configure/Architectures_and_Best_Practices/Cisco_Meraki_Best_Practice_Design/High_Density_Wi-Fi_Deployments",
    "MR28": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR28_Datasheet",
    "MR36": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR36_Datasheet",
    "MR36H": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR36H_Datasheet",
    "MR44": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR44_Datasheet",
    "MR46": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR46_Datasheet",
    "MR76": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR76_Datasheet",
    "MR78": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR78_Datasheet",
    "MR86": "https://documentation.meraki.com/Wireless/Product_Information/Overviews_and_Datasheets/MR86_Datasheet",
    "MR33": "https://meraki.cisco.com/lib/pdf/meraki_datasheet_MR33.pdf",
    "MR30H": "https://meraki.cisco.com/lib/pdf/meraki_datasheet_MR30H.pdf",
    "MR70": "https://meraki.cisco.com/lib/pdf/meraki_datasheet_MR70.pdf",
    "MR30H_INSTALL": "https://documentation.meraki.com/Wireless/Install_and_Get_Started/Installation_Guides/MR30H_Installation_Guide",
    "MR42_INSTALL": "https://documentation.meraki.com/Wireless/Install_and_Get_Started/Installation_Guides/MR42_Installation_Guide",
    "BTU": "https://documentation.meraki.com/Platform_Management/Dashboard_Administration/Operate_and_Maintain/How-Tos/Calculating_BTU_Consumption_for_Cisco_Meraki_Products",
}

TITLES = {
    "FAQ": "Cisco Meraki MR Access Point FAQ",
    "MESH": "Cisco Meraki Mesh Deployment Guide",
    "ROAM": "Cisco Meraki High Density Wi-Fi Deployments",
    "MR28": "Cisco Meraki MR28 Datasheet", "MR36": "Cisco Meraki MR36 Datasheet",
    "MR36H": "Cisco Meraki MR36H Datasheet", "MR44": "Cisco Meraki MR44 Datasheet",
    "MR46": "Cisco Meraki MR46 Datasheet", "MR76": "Cisco Meraki MR76 Datasheet",
    "MR78": "Cisco Meraki MR78 Datasheet", "MR86": "Cisco Meraki MR86 Datasheet",
    "MR33": "Cisco Meraki MR33 Datasheet", "MR30H": "Cisco Meraki MR30H Datasheet",
    "MR70": "Cisco Meraki MR70 Datasheet",
    "MR30H_INSTALL": "Cisco Meraki MR30H Installation Guide",
    "MR42_INSTALL": "Cisco Meraki MR42 Installation Guide",
    "BTU": "How to Calculate BTU Consumption for Meraki Products",
}

ITEMS = []


def add(models, code, kind, value, raw, source, location):
    for model in models:
        ITEMS.append({
            "model": model, "code": code, "kind": kind, "value": value,
            "raw": raw, "url": URLS[source], "title": TITLES[source], "location": location,
        })


# Current platform documentation explicitly applies these capabilities to all Meraki MR APs.
add(
    MODELS, "max_ssids", "number", 15,
    "All Meraki MR access points support up to 15 unique SSIDs.",
    "FAQ", "Frequently Asked Questions — supported features",
)
add(
    MODELS, "centralized_management", "text", "Cisco Meraki cloud dashboard",
    "All Meraki MR access points support cloud-based features; cloud management licenses provide access to supported wireless features.",
    "FAQ", "Frequently Asked Questions — cloud management",
)
add(
    MODELS, "mesh_support", "boolean", True,
    "All Meraki access points support wireless meshing without any additional configuration or licensing.",
    "MESH", "Access Point Capabilities",
)
add(
    MODELS, "fast_roaming", "text", "802.11r fast roaming; PMK/OKC roaming support",
    "Cisco Meraki MR access points support fast roaming technologies, including 802.11r; all are enabled by default except 802.11r.",
    "ROAM", "Roaming in High Density — Enable Fast Roaming",
)

# Current Wi-Fi 6 datasheets: radio rates are the supported over-the-air values with 20 MHz at 2.4 GHz.
RADIO_SPECS = {
    "MR28": (287, 1201, "2x2:2", "2x2:2", 4),
    "MR36": (286, 1201, "2x2:2", "2x2:2", 4),
    "MR36H": (286, 1201, "2x2:2", "2x2:2", 4),
    "MR44": (287, 2402, "2x2:2", "4x4:4", 6),
    "MR46": (574, 2402, "4x4:4", "4x4:4", 8),
    "MR76": (286, 1201, "2x2:2", "2x2:2", 4),
    "MR78": (286, 1201, "2x2:2", "2x2:2", 4),
    "MR86": (574, 2402, "4x4:4", "4x4:4", 8),
}
for model, (rate_2g, rate_5g, mimo_2g, mimo_5g, streams) in RADIO_SPECS.items():
    add((model,), "rate_2g_mbps", "number", rate_2g, f"Up to {rate_2g} Mbps in the 2.4 GHz band", model, "Features — dual-radio aggregate frame rate")
    add((model,), "rate_5g_mbps", "number", rate_5g, f"Up to {rate_5g:,} Mbps in the 5 GHz band", model, "Features — dual-radio aggregate frame rate")
    add((model,), "mimo_2g", "text", mimo_2g, f"2.4 GHz radio: {mimo_2g} MIMO", model, "Product highlights / capabilities")
    add((model,), "mimo_5g", "text", mimo_5g, f"5 GHz radio: {mimo_5g} MIMO", model, "Product highlights / capabilities")
    add((model,), "total_spatial_streams", "number", streams, f"Client-serving spatial streams: {streams} total across 2.4 GHz and 5 GHz radios", model, "Product highlights / capabilities")

DIMENSIONS = {
    "MR28": "202 x 124 x 25.8 mm",
    "MR36": "250 x 120 x 36 mm",
    "MR36H": "155 x 110 x 23 mm",
    "MR44": "306 x 128.4 x 44.3 mm",
    "MR46": "306 x 128.4 x 44.3 mm",
    "MR76": "300 x 153 x 55 mm",
    "MR78": "245 x 115 x 30 mm",
    "MR86": "300 x 153 x 55 mm",
}
for model, value in DIMENSIONS.items():
    add((model,), "dimensions_mm", "text", value, f"Physical dimensions: {value}", model, "Specifications — Physical Dimensions")

add(("MR28",), "ethernet_interfaces", "text", "1 x 10/100/1000BASE-T RJ45; 1 x DC power connector", "Interfaces: 1x 10/100/1000 BASE-T Ethernet (RJ45); 1x DC power connector", "MR28", "Specifications — Interfaces")
add(("MR78",), "ethernet_interfaces", "text", "1 x 10/100/1000BASE-T RJ45", "Interfaces: 1x 10/100/1000 BASE-T Ethernet (RJ45)", "MR78", "Specifications — Interfaces")
add(("MR46",), "max_channel_width_mhz", "number", 80, "20, 40, and 80 MHz channels are supported for 802.11ax", "MR46", "Specifications — 802.11ax capabilities")

# Correct complete antenna descriptions; older imported strings were truncated.
for model in ("MR28", "MR36", "MR36H", "MR78"):
    add((model,), "antenna_gain_dbi", "text", "Internal antennas: 5.4 dBi at 2.4 GHz; 6 dBi at 5 GHz", "Internal antenna: 5.4 dBi gain at 2.4 GHz and 6 dBi gain at 5 GHz", model, "Specifications — Antenna")
add(("MR76",), "antenna_gain_dbi", "text", "External antennas required; supports MA-ANT-20/21/23/25/27", "Compatible antennas: MA-ANT-20/21/23/25/27; antennas are not included", "MR76", "Specifications — Antenna")
add(("MR86",), "antenna_gain_dbi", "text", "External antennas required; supports MA-ANT-20/25/27 and AIR-ANT2513P4M-N", "Compatible antennas: MA-ANT-20/25/27 and AIR-ANT2513P4M-N; antennas are not included", "MR86", "Specifications — Antenna")

# Environmental and hospitality-port facts from current official guides/datasheets.
add(("MR30H",), "operating_temperature_c", "text", "0 to 40 °C", "Operating temperature: 32 °F to 104 °F (0 °C to 40 °C)", "MR30H_INSTALL", "Product Overview — Environment")
add(("MR42",), "operating_temperature_c", "text", "0 to 40 °C", "Operating temperature: 32 °F to 104 °F (0 °C to 40 °C)", "MR42_INSTALL", "Product Overview — Environment")
add(("MR76",), "operating_temperature_c", "text", "-40 to 55 °C", "Operating and storage temperature: -40 °F to 131 °F (-40 °C to 55 °C)", "MR76", "Specifications — Environment")
add(("MR86",), "operating_temperature_c", "text", "-40 to 55 °C", "Operating and storage temperature: -40 °F to 131 °F (-40 °C to 55 °C)", "MR86", "Specifications — Environment")
add(("MR30H",), "poe_output", "text", "1 x 802.3af PoE-out port; disabled when AP input is 802.3af", "1x Gigabit Ethernet RJ45 with 802.3af PoE output; 802.3af operating mode disables PoE out", "MR30H_INSTALL", "Ethernet Ports / Power Source Options")
add(("MR36H",), "poe_output", "text", "1 x 802.3af PoE-out port", "1x Gigabit Ethernet RJ45 with 802.3af Power over Ethernet output", "MR36H", "Specifications — Interfaces")
add(("MR33",), "max_power_consumption_w", "number", 15, "Power consumption: 15 W max (802.3af)", "MR33", "Specifications — Power")
add(("MR33",), "antenna_gain_dbi", "text", "Integrated omni antennas: 3.8 dBi at 2.4 GHz; 3.9 dBi at 5 GHz", "Integrated omni-directional antennas (3.8 dBi gain at 2.4 GHz, 3.9 dBi gain at 5 GHz)", "MR33", "Specifications — Antenna")
add(("MR33",), "dimensions_mm", "text", "215 x 110 x 32 mm", "Physical dimensions: 215 mm x 110 mm x 32 mm", "MR33", "Specifications — Physical Dimensions")
add(("MR33",), "operating_temperature_c", "text", "0 to 40 °C", "Operating temperature: 32 °F to 104 °F (0 °C to 40 °C)", "MR33", "Specifications — Environment")
add(("MR70",), "operating_temperature_c", "text", "-20 to 55 °C", "Operating temperature: -4 °F to 131 °F (-20 °C to 55 °C)", "MR70", "Specifications — Environment")
add(("MR70",), "wireless_security", "text", "WEP; WPA; WPA2-PSK; WPA2-Enterprise with 802.1X; EAP-TLS/TTLS/MSCHAPv2/SIM; TKIP/AES", "WEP, WPA, WPA2-PSK, WPA2-Enterprise with 802.1X; EAP-TLS, EAP-TTLS, EAP-MSCHAPv2, EAP-SIM; TKIP and AES", "MR70", "Specifications — Security")
add(("MR30H",), "wireless_security", "text", "WEP; WPA; WPA2-PSK; WPA2-Enterprise with 802.1X; EAP-TLS/TTLS/MSCHAPv2/SIM; TKIP/AES", "WEP, WPA, WPA2-PSK, WPA2-Enterprise with 802.1X; EAP-TLS, EAP-TTLS, EAP-MSCHAPv2, EAP-SIM; TKIP and AES", "MR30H", "Specifications — Security")


class Command(BaseCommand):
    help = "Import manually verified Cisco Meraki MR access-point gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Meraki").first()
        if not brand:
            raise CommandError("Missing brand: Meraki")
        codes = {item["code"] for item in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for item in ITEMS:
            doc_key = item["url"]
            if doc_key not in documents:
                documents[doc_key], _ = SourceDocument.objects.update_or_create(
                    url=item["url"], document_version="Current official web documentation; accessed 2026-10-20",
                    defaults={
                        "brand": brand, "product": None,
                        "document_type": SourceDocument.DocumentType.SPECIFICATION,
                        "title": item["title"], "region": "Global", "published_date": None,
                        "accessed_date": accessed, "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing Meraki product: {item['model']}")
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
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
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(item["value"]), "unit": definition.unit,
                "raw_value": item["raw"], "source_url": item["url"][:200],
                "source_note": "Manually verified from current official Cisco Meraki documentation.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
            elif item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[doc_key], source_location=item["location"],
                defaults={
                    "source_excerpt": item["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
