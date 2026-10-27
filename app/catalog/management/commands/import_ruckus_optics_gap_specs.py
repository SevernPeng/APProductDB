from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.commscope.com/globalassets/digizuite/61722-ds-ethernet-optics-family.pdf"
SOURCE_VERSION = "Official RUCKUS Ethernet Optics family data sheet; accessed 2026-10-21"
COMPATIBILITY = "RUCKUS ICX switches; exact model and FastIron release support is listed in the official optics compatibility matrix"


def n(model, code, value, raw, location="Key Standards and Features"):
    return {"model": model, "code": code, "kind": "number", "value": value, "raw": raw, "location": location}


def t(model, code, value, raw, location="RUCKUS Ethernet Optics Ordering Information"):
    return {"model": model, "code": code, "kind": "text", "value": value, "raw": raw, "location": location}


ITEMS = []

for model in (
    "10G-SFPP-BXD-S", "10G-SFPP-BXU-S", "10G-SFPP-LR", "10G-SFPP-SR",
    "10G-SFPP-TWX-P-0101", "10G-SFPP-TWX-P-0301",
    "E100G-QSFP28-DAC-0101", "E100G-QSFP28-SR4",
    "E1MG-BXD", "E1MG-BXU", "E1MG-LX-OM", "E1MG-SX-OM", "E1MG-TX",
    "E25G-SFP28-LR", "E25G-SFP28-SR", "E25G-SFP28-TWX-P-00101",
):
    ITEMS.append(t(model, "accessory_compatibility", COMPATIBILITY,
                   "The official data sheet includes product-support matrices for RUCKUS ICX switch families.",
                   "Product Support compatibility matrices"))

ITEMS += [
    n("10G-SFPP-BXD-S", "accessory_wavelength_nm", 1330, "Transmit 1330 nm; receive 1270 nm"),
    n("10G-SFPP-BXD-S", "accessory_max_distance_km", 10, "Maximum cable distance: 10 km SMF"),
    t("10G-SFPP-BXD-S", "accessory_fiber_mode", "Single-mode BiDi/WDM", "Single-strand SMF bidirectional optic"),
    t("10G-SFPP-BXD-S", "operating_temperature_c", "0 to 70 °C", "Standard temperature: 0°C to 70°C"),
    n("10G-SFPP-BXU-S", "accessory_wavelength_nm", 1270, "Transmit 1270 nm; receive 1330 nm"),
    n("10G-SFPP-BXU-S", "accessory_max_distance_km", 10, "Maximum cable distance: 10 km SMF"),
    t("10G-SFPP-BXU-S", "accessory_fiber_mode", "Single-mode BiDi/WDM", "Single-strand SMF bidirectional optic"),
    t("10G-SFPP-BXU-S", "operating_temperature_c", "0 to 70 °C", "Standard temperature: 0°C to 70°C"),
    n("10G-SFPP-LR", "accessory_wavelength_nm", 1310, "Nominal wavelength: 1310 nm"),
    t("10G-SFPP-LR", "operating_temperature_c", "-40 to 85 °C", "Industrial temperature: -40°C to 85°C"),
    n("10G-SFPP-SR", "accessory_wavelength_nm", 850, "Nominal wavelength: 850 nm"),
    t("10G-SFPP-SR", "operating_temperature_c", "-40 to 85 °C", "Industrial temperature: -40°C to 85°C"),

    t("10G-SFPP-TWX-P-0101", "accessory_connector_type", "SFP+ direct attach (both ends)", "Direct Attach SFP+ to SFP+ passive copper cable"),
    t("10G-SFPP-TWX-P-0101", "accessory_fiber_mode", "Passive copper", "Passive copper direct-attach cable"),
    n("10G-SFPP-TWX-P-0101", "accessory_max_distance_km", 0.001, "Fixed cable length: 1 m"),
    t("10G-SFPP-TWX-P-0301", "accessory_connector_type", "SFP+ direct attach (both ends)", "Direct Attach SFP+ to SFP+ passive copper cable"),
    t("10G-SFPP-TWX-P-0301", "accessory_fiber_mode", "Passive copper", "Passive copper direct-attach cable"),
    n("10G-SFPP-TWX-P-0301", "accessory_max_distance_km", 0.003, "Fixed cable length: 3 m"),

    n("E100G-QSFP28-DAC-0101", "accessory_cable_length_m", 1, "Direct-attach QSFP28 passive copper cable, 1 m", "100 GbE QSFP28 DAC cable ordering information"),
    t("E100G-QSFP28-SR4", "accessory_connector_type", "MTP/MPO-12", "100GBASE-SR4 QSFP28 optic, MTP 1x12"),
    n("E100G-QSFP28-SR4", "accessory_wavelength_nm", 850, "Nominal wavelength: 850 nm"),
    n("E100G-QSFP28-SR4", "accessory_max_distance_km", 0.1, "Maximum distance: 100 m over OM4 MMF"),
    t("E100G-QSFP28-SR4", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),

    n("E1MG-BXD", "accessory_wavelength_nm", 1490, "Transmit 1490 nm; receive 1310 nm"),
    n("E1MG-BXD", "accessory_max_distance_km", 10, "Maximum cable distance: 10 km SMF"),
    t("E1MG-BXD", "accessory_fiber_mode", "Single-mode BiDi/WDM", "Single-strand SMF bidirectional optic"),
    t("E1MG-BXD", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    n("E1MG-BXU", "accessory_wavelength_nm", 1310, "Transmit 1310 nm; receive 1490 nm"),
    n("E1MG-BXU", "accessory_max_distance_km", 10, "Maximum cable distance: 10 km SMF"),
    t("E1MG-BXU", "accessory_fiber_mode", "Single-mode BiDi/WDM", "Single-strand SMF bidirectional optic"),
    t("E1MG-BXU", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    n("E1MG-LX-OM", "accessory_wavelength_nm", 1310, "Nominal wavelength: 1310 nm"),
    t("E1MG-LX-OM", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    n("E1MG-SX-OM", "accessory_wavelength_nm", 850, "Nominal wavelength: 850 nm"),
    n("E1MG-SX-OM", "accessory_max_distance_km", 0.55, "Maximum distance: 220 m to 550 m depending on MMF grade"),
    t("E1MG-SX-OM", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    t("E1MG-TX", "accessory_connector_type", "RJ45", "1000BASE-T copper SFP module"),
    t("E1MG-TX", "accessory_fiber_mode", "Copper (1000BASE-T)", "Copper Cat5 module; optical fiber mode does not apply"),
    n("E1MG-TX", "accessory_max_distance_km", 0.1, "Maximum distance: 100 m on Cat5 copper"),
    t("E1MG-TX", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),

    n("E25G-SFP28-LR", "accessory_wavelength_nm", 1310, "Nominal wavelength: 1310 nm"),
    t("E25G-SFP28-LR", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    n("E25G-SFP28-SR", "accessory_wavelength_nm", 850, "Nominal wavelength: 850 nm"),
    n("E25G-SFP28-SR", "accessory_max_distance_km", 0.1, "Maximum distance: 100 m over OM4 MMF"),
    t("E25G-SFP28-SR", "operating_temperature_c", "0 to 70 °C",
      "No alternate temperature range is stated; the data sheet defines the default transceiver range as 0°C to 70°C.",
      "Understanding Part Number Descriptions — Operating Temperature Ranges"),
    t("E25G-SFP28-TWX-P-00101", "accessory_connector_type", "SFP28 direct attach (both ends)", "SFP28 passive direct-attach copper cable"),
    t("E25G-SFP28-TWX-P-00101", "accessory_fiber_mode", "Passive copper", "Passive copper direct-attach cable"),
]


class Command(BaseCommand):
    help = "Import and correct manually verified RUCKUS Ethernet optics and DAC specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Missing brand: RUCKUS")
        codes = {entry["code"] for entry in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL, document_version=SOURCE_VERSION,
            defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                      "title": "RUCKUS Ethernet Optics — High quality transceivers for RUCKUS switches and APs",
                      "region": "Global", "published_date": None, "accessed_date": accessed, "active": True},
        )
        newly_filled = corrected = unchanged = 0
        for entry in ITEMS:
            product = Product.objects.filter(brand=brand, model=entry["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing RUCKUS product: {entry['model']}")
            definition = definitions[entry["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None))
            if entry["kind"] == "number":
                old_value, new_value = (existing.value_number if had else None), Decimal(str(entry["value"]))
            else:
                old_value, new_value = (existing.value_text if had else None), str(entry["value"])
            defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                        "value_boolean": None, "normalized_value": str(entry["value"]), "unit": definition.unit,
                        "raw_value": entry["raw"], "source_url": SOURCE_URL[:200],
                        "source_note": "Manually verified from the official RUCKUS Ethernet Optics family data sheet.",
                        "verified_date": accessed}
            if entry["kind"] == "number": defaults["value_number"] = new_value
            else: defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had: newly_filled += 1
            elif old_value != new_value: corrected += 1
            else: unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=source, source_location=entry["location"],
                defaults={"source_excerpt": entry["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                          "verified_at": timezone.now()},
            )
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"))
