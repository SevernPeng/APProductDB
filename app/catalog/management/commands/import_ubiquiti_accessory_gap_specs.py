from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "POE48": ("https://techspecs.ui.com/uisp/accessory-tech/poe-48", "Ubiquiti POE-48 official Tech Specs"),
    "POE24": ("https://techspecs.ui.com/uisp/accessory-tech/uacc-adapter-poe-24-12w?subcategory=all-accessory-tech", "Ubiquiti UACC-Adapter-PoE-24-12W official Tech Specs"),
    "POE25": ("https://techspecs.ui.com/unifi/accessories/uacc-poe-plus-2-5g?subcategory=accessories-poe-power", "Ubiquiti UACC-PoE+-2.5G official Tech Specs"),
    "POE10": ("https://techspecs.ui.com/unifi/accessories/uacc-poe-plus-plus-10g?subcategory=accessories-poe-power", "Ubiquiti UACC-PoE++-10G official Tech Specs"),
    "AE": ("https://techspecs.ui.com/unifi/accessories/uacc-ae?subcategory=accessories-cables-dacs", "Ubiquiti UACC-AE official Tech Specs"),
    "RACK": ("https://techspecs.ui.com/unifi/accessories/uacc-rack-shelf-fd?subcategory=accessories-rack-mount", "Ubiquiti Full Depth Rack Shelf official Tech Specs"),
    "CM1": ("https://techspecs.ui.com/unifi/accessories/rj45-to-sfp-module?subcategory=accessories-modules-fiber", "Ubiquiti UACC-CM-RJ45 official Tech Specs"),
    "CM10": ("https://techspecs.ui.com/unifi/accessories/uacc-cm-rj45-mg?subcategory=accessories-cables-dacs", "Ubiquiti UACC-CM-RJ45-MG official Tech Specs"),
    "DAC10": ("https://techspecs.ui.com/unifi/accessories/10gbps-direct-attach-cable", "Ubiquiti 10 Gbps Direct Attach Cable official Tech Specs"),
    "DAC25": ("https://techspecs.ui.com/unifi/accessories/25gbps-direct-attach-cable?subcategory=accessories-modules-fiber", "Ubiquiti 25 Gbps Direct Attach Cable official Tech Specs"),
    "DAC100": ("https://techspecs.ui.com/unifi/accessories/uacc-dac-qsfp28?subcategory=accessories-modules-fiber", "Ubiquiti 100 Gbps Direct Attach Cable official Tech Specs"),
    "MM1": ("https://techspecs.ui.com/unifi/accessories/1-gbps-multi-mode-optical-module", "Ubiquiti 1 Gbps Multi-Mode Optical Module official Tech Specs"),
    "MM10": ("https://techspecs.ui.com/unifi/accessories/10-gbps-multi-mode-optical-module", "Ubiquiti 10 Gbps Multi-Mode Optical Module official Tech Specs"),
    "SM1": ("https://techspecs.ui.com/unifi/accessories/1-gbps-bidirectional-single-mode-optical-module", "Ubiquiti 1 Gbps BiDi Single-Mode Optical Module official Tech Specs"),
    "SM10S": ("https://techspecs.ui.com/unifi/accessories/uacc-om-sm-10g-s", "Ubiquiti UACC-OM-SM-10G-S official Tech Specs"),
    "SM10D": ("https://techspecs.ui.com/unifi/accessories/uacc-om-sm-10g-d", "Ubiquiti UACC-OM-SM-10G-D official Tech Specs"),
    "SFP28LR": ("https://techspecs.ui.com/unifi/accessories/uacc-om-sfp28-lr?subcategory=accessories-modules-fiber", "Ubiquiti UACC-OM-SFP28-LR official Tech Specs"),
    "SFP28SR": ("https://techspecs.ui.com/unifi/accessories/25gbps-multi-mode-optical-module", "Ubiquiti UACC-OM-SFP28-SR official Tech Specs"),
    "QSFP28": ("https://techspecs.ui.com/unifi/accessories/uacc-om-qsfp28-sr4", "Ubiquiti UACC-OM-QSFP28-SR4 official Tech Specs"),
}

ITEMS = []


def add(model, code, kind, value, raw, source, location):
    ITEMS.append({"model": model, "code": code, "kind": kind, "value": value, "raw": raw, "source": source, "location": location})


def text(model, code, value, raw, source, location):
    add(model, code, "text", value, raw, source, location)


def number(model, code, value, raw, source, location):
    add(model, code, "number", value, raw, source, location)


def common_data(model, source, interface, connector, medium, rate, distance, power, compatibility):
    text(model, "accessory_interface_type", interface, f"Interface type: {interface}", source, "Technical Specifications — Interface")
    text(model, "accessory_connector_type", connector, f"Connector type: {connector}", source, "Technical Specifications — Connector")
    text(model, "accessory_fiber_mode", medium, f"Cable/fiber medium: {medium}", source, "Technical Specifications — Media")
    number(model, "accessory_data_rate_gbps", rate, f"Maximum supported data rate: {rate} Gbps", source, "Technical Specifications — Supported Data Rate")
    if distance is not None:
        number(model, "accessory_max_distance_km", distance, f"Maximum supported distance: {distance} km", source, "Technical Specifications — Supported Distance")
    if power is not None:
        number(model, "accessory_power_w", power, f"Maximum power consumption: {power}W", source, "Technical Specifications — Max. Power Consumption")
    text(model, "accessory_compatibility", compatibility, compatibility, source, "Overview / Technical Specifications — Compatibility")
    text(model, "operating_temperature_c", "0 to 70 °C", "Ambient operating temperature: 0 to 70° C", source, "Technical Specifications — Environment")


# PoE adapters and active media converter.
text("POE-48", "accessory_compatibility", "24 V passive-PoE devices requiring up to 24 W over Gigabit Ethernet", "48V DC, 0.5A output; GbE LAN; passive 2-pair powering", "POE48", "Overview / Technical Specifications")
text("POE-48", "accessory_input_power", "100–240 V AC, 50/60 Hz", "Rated voltage: 100–240V AC, 50/60Hz", "POE48", "Technical Specifications — Rated Voltage")
text("POE-48", "accessory_output_power", "48 V DC at 0.5 A", "Output: 48V DC @ 0.5A", "POE48", "Technical Specifications — Output")
text("POE-48", "accessory_poe_standard", "Passive PoE, 2-pair", "Power method: passive PoE, 2-pair", "POE48", "Technical Specifications — PoE Method")
number("POE-48", "accessory_power_w", 24, "Maximum output: 48V DC × 0.5A = 24W", "POE48", "Technical Specifications — Output")
number("POE-48", "accessory_data_rate_gbps", 1, "GbE LAN: yes", "POE48", "Technical Specifications — LAN Activity Indicator")

text("UACC-Adapter-PoE-24-12W", "accessory_compatibility", "24 V passive-PoE devices requiring up to 12 W over Gigabit Ethernet", "24V DC, 0.5A output; GbE LAN; passive 2-pair powering", "POE24", "Overview / Technical Specifications")
text("UACC-Adapter-PoE-24-12W", "accessory_input_power", "100–240 V AC, 50/60 Hz", "Rated voltage: 100–240V AC, 50/60Hz", "POE24", "Technical Specifications — Rated Voltage")
text("UACC-Adapter-PoE-24-12W", "accessory_output_power", "24 V DC at 0.5 A", "Output: 24V DC @ 0.5A", "POE24", "Technical Specifications — Output")
text("UACC-Adapter-PoE-24-12W", "accessory_poe_standard", "Passive PoE, 2-pair", "Power method: passive PoE, 2-pair", "POE24", "Technical Specifications — PoE Method")
number("UACC-Adapter-PoE-24-12W", "accessory_data_rate_gbps", 1, "GbE LAN: yes", "POE24", "Technical Specifications — LAN")

text("UACC-PoE+-2.5G", "accessory_compatibility", "IEEE 802.3af/at powered devices over Ethernet up to 2.5 Gbps", "30W PoE+ adapter with 2.5 GbE data rate", "POE25", "Overview")
text("UACC-PoE+-2.5G", "accessory_input_power", "100–240 V AC, 50/60 Hz", "Rated voltage: 100–240V AC, 50/60Hz", "POE25", "Technical Specifications — Rated Voltage")
text("UACC-PoE+-2.5G", "accessory_output_power", "48 V DC at 0.65 A", "Output: 48V DC @ 0.65A", "POE25", "Technical Specifications — Output")
text("UACC-PoE+-2.5G", "accessory_poe_standard", "IEEE 802.3af/at (PoE/PoE+)", "PoE standard: IEEE 802.3af/at", "POE25", "Technical Specifications — PoE Standard")
number("UACC-PoE+-2.5G", "accessory_power_w", 30, "PoE+ adapter: 30W", "POE25", "Overview")
number("UACC-PoE+-2.5G", "accessory_data_rate_gbps", 2.5, "Maximum data rate: 2.5 Gbps", "POE25", "Overview")
text("UACC-PoE+-2.5G", "accessory_interface_type", "2 x RJ45 Ethernet", "Networking interfaces: two RJ45 Ethernet ports", "POE25", "Overview / Port Layout")
text("UACC-PoE+-2.5G", "accessory_connector_type", "RJ45", "Connector type: RJ45", "POE25", "Overview / Port Layout")
text("UACC-PoE+-2.5G", "dimensions_mm", "93 x 62 x 35 mm", "Dimensions: 93 x 62 x 35 mm", "POE25", "Overview — Dimensions")
text("UACC-PoE+-2.5G", "operating_temperature_c", "0 to 40 °C", "Ambient operating temperature: 0 to 40° C", "POE25", "Technical Specifications — Environment")

text("UACC-PoE++-10G", "accessory_compatibility", "IEEE 802.3af/at/bt Type 3 powered devices over Ethernet up to 10 Gbps", "60W PoE++ adapter with 10 GbE data rate", "POE10", "Overview")
text("UACC-PoE++-10G", "accessory_input_power", "100–240 V AC, 50/60 Hz", "Rated voltage: 100–240V AC, 50/60Hz", "POE10", "Technical Specifications — Rated Voltage")
text("UACC-PoE++-10G", "accessory_output_power", "54 V DC at 1.12 A", "Output: 54V DC @ 1.12A", "POE10", "Technical Specifications — Output")
text("UACC-PoE++-10G", "accessory_poe_standard", "IEEE 802.3af/at/bt Type 3 (PoE++)", "PoE standard: IEEE 802.3af/at/bt Type 3", "POE10", "Technical Specifications — PoE Standard")
number("UACC-PoE++-10G", "accessory_power_w", 60, "Max. PoE power: 60W", "POE10", "Overview")
number("UACC-PoE++-10G", "accessory_data_rate_gbps", 10, "Maximum data rate: 10 Gbps", "POE10", "Overview")
text("UACC-PoE++-10G", "dimensions_mm", "106 x 63 x 34 mm", "Dimensions: 106 x 63 x 34 mm", "POE10", "Overview — Dimensions")

text("UACC-AE", "accessory_compatibility", "Devices using 1G SFP and GbE RJ45 media conversion; powered by UniFi PoE or 24 V passive PoE", "1G SFP and GbE RJ45 interfaces; PoE/passive PoE input", "AE", "Overview / Technical Specifications")
text("UACC-AE", "accessory_interface_type", "1 x 1G SFP; 1 x GbE RJ45", "Networking interfaces: one 1G SFP and one GbE RJ45", "AE", "Overview — Port Layout")
text("UACC-AE", "accessory_connector_type", "SFP to RJ45", "Connectors: SFP and RJ45", "AE", "Overview — Port Layout")
text("UACC-AE", "accessory_input_power", "PoE or 24 V passive PoE; 16–57 V DC", "Power method: PoE, passive PoE 24V; supported voltage range: 16–57V DC", "AE", "Technical Specifications — Power")
text("UACC-AE", "accessory_poe_standard", "PoE / 24 V passive PoE", "Power method: PoE, passive PoE 24V", "AE", "Technical Specifications — Power Method")
number("UACC-AE", "accessory_power_w", 1.5, "Max. power consumption: 1.5W", "AE", "Technical Specifications — Max. Power Consumption")

# Full-depth shelf: the database keeps the shorter historical model label.
text("UACC-Rack-Shelf", "accessory_compatibility", "UACC-Rack-42U and standard 19-inch racks with compatible side mounting", "Full Depth Rack Shelf; compatible with the Ubiquiti 42U Rack Cabinet", "RACK", "Overview")
number("UACC-Rack-Shelf", "accessory_rack_units", 1, "Rack height: 1U", "RACK", "Overview — Rack Height")

# Copper SFP/QSFP adapters and direct-attach cables.
common_data("UACC-CM-RJ45", "CM1", "SFP", "RJ45", "Copper", 1, 0.1, 1.2, "Devices with a compatible SFP port; 10/100/1000 Mbps copper Ethernet over RJ45")
common_data("UACC-CM-RJ45-MG", "CM10", "SFP+", "RJ45", "Copper", 10, 0.1, 1.9, "Devices with a compatible SFP+ port; 1/2.5/5/10 Gbps copper Ethernet over Cat 6A RJ45")
common_data("UACC-DAC-SFP10-1M", "DAC10", "SFP+", "SFP+ to SFP+", "Copper", 10, 0.001, None, "Devices with compatible SFP+ ports; supports 1 and 10 Gbps")
common_data("UACC-DAC-SFP10-3M", "DAC10", "SFP+", "SFP+ to SFP+", "Copper", 10, 0.003, None, "Devices with compatible SFP+ ports; supports 1 and 10 Gbps")
common_data("UACC-DAC-SFP28-1M", "DAC25", "SFP28", "SFP28 to SFP28", "Copper", 25, 0.001, None, "Devices with compatible SFP28, SFP+, or SFP ports; supports 1, 10, and 25 Gbps")
common_data("UACC-DAC-QSFP28-1M", "DAC100", "QSFP28", "QSFP28 to QSFP28", "Copper", 100, 0.001, 2.5, "Devices with compatible QSFP28 or QSFP+ ports; supports 40 and 100 Gbps")


def optical(model, source, interface, connector, fiber, rate, distance, wavelength, power, compatibility):
    common_data(model, source, interface, connector, fiber, rate, distance, power, compatibility)
    if wavelength is not None:
        number(model, "accessory_wavelength_nm", wavelength, f"TX/RX wavelength: {wavelength} nm", source, "Technical Specifications — TX/RX Wavelength")


optical("UACC-OM-MM-1G-D", "MM1", "SFP", "Duplex LC UPC", "Multi-mode", 1, 0.55, 850, 0.66, "Devices with a compatible SFP port and duplex multi-mode fiber")
optical("UACC-OM-MM-10G-D", "MM10", "SFP+", "Duplex LC UPC", "Multi-mode", 10, 0.4, 850, 0.8, "Devices with a compatible SFP+ port and duplex OM3/OM4 multi-mode fiber")
optical("UACC-OM-SM-1G-S", "SM1", "SFP", "Simplex LC UPC", "Single-mode", 1, 3, None, 0.66, "Devices with a compatible SFP port and simplex single-mode fiber; bidirectional matched pair")
optical("UACC-OM-SM-10G-S", "SM10S", "SFP+", "Simplex LC UPC", "Single-mode", 10, 10, None, 1, "Devices with a compatible SFP+ port and simplex single-mode fiber; bidirectional matched pair")
optical("UACC-OM-SM-10G-D", "SM10D", "SFP+", "Duplex LC UPC", "Single-mode", 10, 10, 1310, 1, "Devices with a compatible SFP+ port and duplex single-mode fiber")
optical("UACC-OM-SFP28-LR", "SFP28LR", "SFP28", "Duplex LC UPC", "Single-mode", 25, 10, 1310, 1.3, "Devices with a compatible SFP28 port and duplex single-mode fiber; supports 1/10/25 Gbps")
optical("UACC-OM-SFP28-SR", "SFP28SR", "SFP28", "Duplex LC UPC", "Multi-mode", 25, 0.1, 850, 0.8, "Devices with a compatible SFP28 port and duplex OM3/OM4 multi-mode fiber; supports 1/10/25 Gbps")
optical("UACC-OM-QSFP28-SR4", "QSFP28", "QSFP28", "MPO-12 Type B UPC", "Multi-mode", 100, 0.1, 850, 2.5, "Devices with a compatible QSFP28 port and MPO-12 OM3/OM4 multi-mode fiber; supports 40/100 Gbps")


class Command(BaseCommand):
    help = "Import manually verified Ubiquiti accessory specifications from official Tech Specs pages."

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
                    document_version="Current official Ubiquiti Tech Specs page; accessed 2026-10-21",
                    defaults={
                        "brand": brand,
                        "product": None,
                        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
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
                "source_note": "Manually verified from the current official Ubiquiti Tech Specs page.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
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
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
