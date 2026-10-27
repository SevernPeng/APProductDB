from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    Brand,
    Product,
    ProductSpec,
    ProductType,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
)


SOURCE_URL = "https://instant-on.hpe.com/files/HPE-NW-IO_WI-FI-6_data_sheet_A4_0825.pdf"


def ap_specs(
    rate_2g,
    rate_5g,
    mimo_2g,
    mimo_5g,
    clients,
    interface,
    power,
    watts,
    dimensions,
    antenna_type,
    antenna_gain,
    *,
    width=80,
    temperature="0 to 40 °C",
    ip_rating=None,
    poe_output=None,
):
    values = {
        "supported_bands": ("text", "2.4 GHz and 5 GHz"),
        "total_spatial_streams": ("number", mimo_2g + mimo_5g),
        "mimo_2g": ("text", f"{mimo_2g}x{mimo_2g} MIMO"),
        "mimo_5g": ("text", f"{mimo_5g}x{mimo_5g} MIMO"),
        "rate_2g_mbps": ("number", rate_2g),
        "rate_5g_mbps": ("number", rate_5g),
        "max_channel_width_mhz": ("number", width),
        "ethernet_interfaces": ("text", interface),
        "power_method": ("text", power),
        "max_clients": ("number", clients),
        "antenna_type": ("text", antenna_type),
        "antenna_gain_dbi": ("text", antenna_gain),
        "centralized_management": ("text", "Instant On mobile application and cloud portal"),
        "mesh_support": ("boolean", True),
        "wireless_security": ("text", "WPA2, WPA3 and OWE"),
        "max_power_consumption_w": ("number", watts),
        "dimensions_mm": ("text", dimensions),
        "operating_temperature_c": ("text", temperature),
    }
    if ip_rating:
        values["ip_rating"] = ("text", ip_rating)
    if poe_output:
        values["poe_output"] = ("text", poe_output)
    return values


MODELS = {
    "AP21": ap_specs(
        300, 1200, 2, 2, 50,
        "1 x 1GbE Base-T uplink",
        "802.3af PoE or 12 V DC",
        10.9,
        "145 x 145 x 51 mm",
        "Dual omni-directional 2x2 MIMO",
        "1.7 dBi (2.4 GHz); 4.8 dBi (5 GHz)",
    ),
    "AP22": ap_specs(
        574, 1200, 2, 2, 75,
        "1 x 1GbE Base-T uplink",
        "802.3af PoE or 12 V DC",
        10.1,
        "153 x 153 x 37 mm",
        "Dual omni-directional 2x2 MIMO",
        "4.9 dBi (2.4 GHz); 5.7 dBi (5 GHz)",
    ),
    "AP22D": ap_specs(
        574, 1200, 2, 2, 75,
        "1 x 2.5GbE PoE uplink; 2 x 1GbE PoE downlink; 2 x 1GbE downlink",
        "802.3bt PoE (full functionality), 802.3at PoE (limited), or 48 V DC",
        51,
        "86 x 47 x 150 mm",
        "Dual semi-directional 2x2 MIMO",
        "5.2 dBi (2.4 GHz); 5.4 dBi (5 GHz)",
        poe_output="2 x 15 W 802.3af PoE output",
    ),
    "AP25": ap_specs(
        574, 4800, 2, 4, 100,
        "1 x 2.5GbE Base-T PoE uplink",
        "802.3at PoE or 12 V DC",
        20.1,
        "200 x 200 x 45 mm",
        "Down-tilt omni-directional antennas",
        "3.7 dBi (2.4 GHz); 4.5 dBi (5 GHz)",
        width=160,
    ),
    "AP27": ap_specs(
        574, 1200, 2, 2, 75,
        "1 x 1GbE Base-T PoE uplink",
        "802.3at PoE",
        14.6,
        "180 x 232 x 120 mm",
        "Dual omni-directional 2x2 MIMO",
        "3.2 dBi (2.4 GHz); 5.4 dBi (5 GHz)",
        temperature="-40 to 65 °C",
        ip_rating="IP67",
    ),
}


class Command(BaseCommand):
    help = "Import manually verified HPE Networking Instant On Wi-Fi 6 AP specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Instant On").first()
        if not brand:
            raise CommandError("Brand 'Instant On' was not found.")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="2025-08",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "HPE Networking Instant On Access Point Series Wi-Fi 6 Data Sheet",
                "region": "Global",
                "published_date": date(2025, 8, 1),
                "accessed_date": accessed,
                "active": True,
            },
        )
        definitions = {
            definition.code: definition
            for definition in SpecDefinition.objects.filter(
                code__in={code for specs in MODELS.values() for code in specs}
            )
        }
        wall_plate = ProductType.objects.get(
            category__slug="access-point", code="wall_plate", active=True
        )
        updated = 0
        for model, values in MODELS.items():
            product = Product.objects.filter(
                brand=brand, model=model, is_published=True
            ).first()
            if not product:
                raise CommandError(f"Missing published product: {model}")
            if model == "AP22D" and product.product_type_id != wall_plate.id:
                product.product_type = wall_plate
                product.ap_type = "wall_plate"
                product.save(update_fields=("product_type", "ap_type", "updated_at"))
            for code, (kind, value) in values.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": str(value),
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the latest official Wi-Fi 6 series datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Technical specifications table - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS)}"))
