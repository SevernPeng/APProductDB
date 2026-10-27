from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value):
    return "boolean", value


MANAGEMENT = t("UniFi Network management over Ethernet")
FAST_ROAMING = t("802.11r Fast Roaming; 802.11v BSS Transition Management; 802.11k RRM")
SECURITY = t("Private pre-shared keys; RadSec; dynamic RADIUS-assigned VLAN; guest and client isolation")


def ap(
    url,
    bands,
    streams,
    rates,
    mimo,
    width,
    interface,
    power,
    clients,
    gain,
    watts,
    dimensions,
    temperature,
    **extra,
):
    values = {
        "supported_bands": t(bands),
        "total_spatial_streams": n(streams),
        "rate_2g_mbps": n(rates[0]),
        "rate_5g_mbps": n(rates[1]),
        "mimo_2g": t(mimo[0]),
        "mimo_5g": t(mimo[1]),
        "max_channel_width_mhz": n(width),
        "ethernet_interfaces": t(interface),
        "power_method": t(power),
        "max_clients": n(clients),
        "antenna_gain_dbi": t(gain),
        "max_ssids": n(8),
        "centralized_management": MANAGEMENT,
        "mesh_support": b(True),
        "fast_roaming": FAST_ROAMING,
        "wireless_security": SECURITY,
        "max_power_consumption_w": n(watts),
        "dimensions_mm": t(dimensions),
        "operating_temperature_c": t(temperature),
    }
    if len(rates) == 3:
        values["rate_6g_mbps"] = n(rates[2])
        values["mimo_6g"] = t(mimo[2])
    for code, value in extra.items():
        values[code] = value
    return {"url": url, "values": values}


MODELS = {
    "E7": ap(
        "https://techspecs.ui.com/unifi/wifi/e7",
        "2.4 GHz, 5 GHz and 6 GHz", 10, (688, 8600, 11400),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO"),
        320, "1 x 10GbE RJ45; 1 x 1GbE RJ45", "PoE++", 1000,
        "5 dBi (2.4 GHz); 6 dBi (5 GHz); 6 dBi (6 GHz)", 43,
        "250 x 250 x 43.5 mm", "-30 to 50 °C",
    ),
    "U7-Lite": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-lite",
        "2.4 GHz and 5 GHz", 4, (688, 4300),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        240, "1 x 2.5GbE RJ45", "PoE", 200,
        "4 dBi (2.4 GHz); 5 dBi (5 GHz)", 13,
        "171.5 mm diameter x 33 mm", "-30 to 40 °C",
    ),
    "U7-Pro": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro",
        "2.4 GHz, 5 GHz and 6 GHz", 6, (688, 4300, 5800),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 2.5GbE RJ45", "PoE+", 300,
        "4 dBi (2.4 GHz); 6 dBi (5 GHz); 5.8 dBi (6 GHz)", 21,
        "206 mm diameter x 46 mm", "-30 to 40 °C",
    ),
    "U7-PRO-MAX": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro-max",
        "2.4 GHz, 5 GHz and 6 GHz", 8, (688, 8600, 5800),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 2.5GbE RJ45", "PoE+", 500,
        "4 dBi (2.4 GHz); 6 dBi (5 GHz); 5.9 dBi (6 GHz)", 25,
        "206 mm diameter x 46 mm", "-30 to 50 °C",
    ),
    "U7-Pro-XG": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro-xg",
        "2.4 GHz, 5 GHz and 6 GHz", 6, (688, 4300, 5800),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 10GbE RJ45", "PoE+", 300,
        "4 dBi (2.4 GHz); 5 dBi (5 GHz); 6 dBi (6 GHz)", 22,
        "206 mm diameter x 32.5 mm", "-30 to 40 °C",
    ),
    "U7-Pro-XGS": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro-xgs",
        "2.4 GHz, 5 GHz and 6 GHz", 8, (688, 8600, 5800),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 10GbE RJ45", "PoE++", 500,
        "4 dBi (2.4 GHz); 6 dBi (5 GHz); 6 dBi (6 GHz)", 29,
        "215 mm diameter x 32.5 mm", "-30 to 40 °C",
    ),
    "U7-IW": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-iw",
        "2.4 GHz and 5 GHz", 4, (688, 4300),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        240, "3 x 2.5GbE RJ45", "PoE; PoE+ required for PoE output", 200,
        "4 dBi (2.4 GHz); 8 dBi (5 GHz)", 13,
        "137 x 98.7 x 30.2 mm", "-30 to 40 °C",
        poe_output=t("1 x PoE output; PoE+ input required"),
    ),
    "U7-In-Wall": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-iw",
        "2.4 GHz and 5 GHz", 4, (688, 4300),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        240, "3 x 2.5GbE RJ45", "PoE; PoE+ required for PoE output", 200,
        "4 dBi (2.4 GHz); 8 dBi (5 GHz)", 13,
        "137 x 98.7 x 30.2 mm", "-30 to 40 °C",
        poe_output=t("1 x PoE output; PoE+ input required"),
    ),
    "U7-Pro-Wall": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro-wall",
        "2.4 GHz, 5 GHz and 6 GHz", 6, (688, 4300, 5800),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 2.5GbE RJ45", "PoE+", 300,
        "4 dBi (2.4 GHz); 5 dBi (5 GHz); 6 dBi (6 GHz)", 22,
        "150 x 103 x 36 mm", "-30 to 60 °C",
    ),
    "U7-Outdoor": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-outdoor",
        "2.4 GHz and 5 GHz", 4, (688, 4300),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        240, "1 x 2.5GbE RJ45", "PoE+", 250,
        "Internal directional: 8 dBi (2.4 GHz), 12.5 dBi (5 GHz); external omni: 3 dBi, 4 dBi",
        19, "170 x 208 x 54.5 mm", "-30 to 60 °C",
        ip_rating=t("IPX6"), antenna_type=t("Internal directional antenna or external omni antennas"),
        wireless_range=t("465 m² coverage area"),
    ),
    "U7-Pro-Outdoor": ap(
        "https://techspecs.ui.com/unifi/wifi/u7-pro-outdoor-us",
        "2.4 GHz, 5 GHz and 6 GHz", 6, (688, 4300, 5800),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        320, "1 x 2.5GbE RJ45", "PoE+", 300,
        "Internal directional: 8 dBi (2.4 GHz), 11 dBi (5 GHz), 10 dBi (6 GHz); external omni: 6 dBi, 8 dBi",
        21, "170 x 208 x 66.5 mm without mount", "-30 to 60 °C",
        ip_rating=t("IPX6; IP67 with cable-gland door kit"),
        antenna_type=t("Internal directional antenna or external omni antennas"),
        wireless_range=t("465 m² coverage area"),
    ),
    "U6+": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-plus",
        "2.4 GHz and 5 GHz", 4, (573.5, 2400),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        160, "1 x 1GbE RJ45", "PoE", 300,
        "3 dBi (2.4 GHz); 5.4 dBi (5 GHz)", 9,
        "160 mm diameter x 33 mm", "-30 to 60 °C",
    ),
    "U6-Pro": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-pro",
        "2.4 GHz and 5 GHz", 6, (573.5, 4800),
        ("2x2 UL MU-MIMO", "4x4 DL/UL MU-MIMO"),
        160, "1 x 1GbE RJ45", "PoE", 250,
        "4 dBi (2.4 GHz); 6 dBi (5 GHz)", 13,
        "197 mm diameter x 35 mm", "-30 to 60 °C",
        ip_rating=t("IP54"),
    ),
    "U6-LR": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-lr",
        "2.4 GHz and 5 GHz", 8, (600, 2400),
        ("4x4 SU-MIMO", "4x4 DL/UL MU-MIMO"),
        160, "1 x 1GbE RJ45", "PoE+", 350,
        "4 dBi (2.4 GHz); 5.5 dBi (5 GHz)", 18.5,
        "220 mm diameter x 48 mm", "-30 to 60 °C",
        ip_rating=t("IP54"),
    ),
    "U6-IW": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-iw",
        "2.4 GHz and 5 GHz", 6, (573.5, 4800),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO"),
        160, "1 x 1GbE data-in; 4 x 1GbE data-out", "PoE; PoE+ required for PoE output", 250,
        "5 dBi (2.4 GHz); 5.9 dBi (5 GHz)", 13,
        "139.7 x 96 x 31.2 mm", "-30 to 60 °C",
        poe_output=t("1 x PoE output among four GbE data-out ports; PoE+ input required"),
    ),
    "U6-Extender": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-extender",
        "2.4 GHz and 5 GHz", 6, (573.5, 4800),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO"),
        160, "Wireless mesh uplink; no Ethernet interface listed", "100-240 V AC wall outlet", 250,
        "5 dBi (2.4 GHz); 6 dBi (5 GHz)", 11,
        "169.7 x 112.2 x 32.2 mm (US)", "-10 to 50 °C",
    ),
    "U6-MESH-PRO": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-mesh-pro",
        "2.4 GHz and 5 GHz", 4, (573.5, 2400),
        ("2x2 DL/UL MU-MIMO", "2x2 DL/UL MU-MIMO"),
        160, "2 x 1GbE RJ45", "PoE; adapter included", 250,
        "8 dBi (2.4 GHz); 8 dBi (5 GHz)", 9,
        "343.2 x 181.2 x 60.2 mm", "-30 to 60 °C",
        ip_rating=t("IPX6"), antenna_type=t("Integrated directional antennas"),
        wireless_range=t("185 m² coverage area"),
    ),
    "U6-Mesh": ap(
        "https://techspecs.ui.com/unifi/wifi/u6-mesh",
        "2.4 GHz and 5 GHz", 6, (573.5, 4800),
        ("2x2 DL/UL MU-MIMO", "4x4 DL/UL MU-MIMO"),
        160, "1 x 1GbE RJ45", "PoE; adapter included", 250,
        "3 dBi (2.4 GHz); 5 dBi (5 GHz)", 13,
        "48.5 mm diameter x 159.5 mm", "-30 to 60 °C",
        ip_rating=t("IPX5"), antenna_type=t("Integrated omni-directional antennas"),
        wireless_range=t("140 m² coverage area"),
    ),
    "UAP-AC-PRO": ap(
        "https://techspecs.ui.com/unifi/wifi/uap-ac-pro",
        "2.4 GHz and 5 GHz", 6, (450, 1300),
        ("3x3 DL MU-MIMO", "3x3 DL MU-MIMO"),
        80, "2 x 1GbE RJ45", "PoE; adapter included", 250,
        "3 dBi (2.4 GHz); 3 dBi (5 GHz)", 9,
        "196.7 mm diameter x 35 mm", "-10 to 70 °C",
    ),
    "UAP-AC-LR": ap(
        "https://techspecs.ui.com/unifi/wifi/unifi-ac-lr",
        "2.4 GHz and 5 GHz", 5, (450, 867),
        ("3x3 DL MU-MIMO", "2x2 DL MU-MIMO"),
        80, "1 x 1GbE RJ45", "PoE; adapter included", 250,
        "3 dBi (2.4 GHz); 3 dBi (5 GHz)", 6.5,
        "175.7 mm diameter x 43.2 mm", "-10 to 70 °C",
    ),
    "UAP-AC-Lite": ap(
        "https://techspecs.ui.com/unifi/wifi/uap-ac-lite",
        "2.4 GHz and 5 GHz", 4, (300, 867),
        ("2x2 DL MU-MIMO", "2x2 DL MU-MIMO"),
        80, "1 x 1GbE RJ45", "PoE; adapter included", 250,
        "3 dBi (2.4 GHz); 3 dBi (5 GHz)", 6.5,
        "160 mm diameter x 31.45 mm", "-10 to 70 °C",
    ),
    "UAP-AC-IW": ap(
        "https://techspecs.ui.com/unifi/wifi/uap-ac-iw",
        "2.4 GHz and 5 GHz", 4, (300, 867),
        ("2x2 DL MU-MIMO", "2x2 DL MU-MIMO"),
        80, "3 x 1GbE RJ45", "PoE; PoE+ required for PoE passthrough", 250,
        "1 dBi (2.4 GHz); 2 dBi (5 GHz)", 7,
        "139.7 x 86.7 x 25.8 mm", "-10 to 50 °C",
        poe_output=t("PoE passthrough; PoE+ input required"),
    ),
    "UAP-AC-M": ap(
        "https://techspecs.ui.com/unifi/wifi/uap-ac-mesh",
        "2.4 GHz and 5 GHz", 4, (300, 867),
        ("2x2 DL MU-MIMO", "2x2 DL MU-MIMO"),
        80, "1 x 1GbE RJ45", "PoE; adapter included", 200,
        "3 dBi (2.4 GHz); 4 dBi (5 GHz)", 8.5,
        "353 x 46 x 34.4 mm", "-30 to 70 °C",
        ip_rating=t("IPX4"), antenna_type=t("External omni-directional antennas"),
        wireless_range=t("140 m² coverage area"),
    ),
    "UAP-AC-Mesh": ap(
        "https://techspecs.ui.com/unifi/wifi/uap-ac-mesh",
        "2.4 GHz and 5 GHz", 4, (300, 867),
        ("2x2 DL MU-MIMO", "2x2 DL MU-MIMO"),
        80, "1 x 1GbE RJ45", "PoE; adapter included", 200,
        "3 dBi (2.4 GHz); 4 dBi (5 GHz)", 8.5,
        "353 x 46 x 34.4 mm", "-30 to 70 °C",
        ip_rating=t("IPX4"), antenna_type=t("External omni-directional antennas"),
        wireless_range=t("140 m² coverage area"),
    ),
    "UAP-AC-M-PRO": ap(
        "https://techspecs.ui.com/unifi/wifi/unifi-ac-mesh-pro-ap",
        "2.4 GHz and 5 GHz", 6, (450, 1300),
        ("3x3 DL MU-MIMO", "3x3 DL MU-MIMO"),
        80, "2 x 1GbE RJ45", "PoE; adapter included", 250,
        "8 dBi (2.4 GHz); 8 dBi (5 GHz)", 9,
        "343.2 x 181.2 x 60.2 mm", "-40 to 70 °C",
        ip_rating=t("IPX4"), antenna_type=t("Integrated directional antennas"),
        wireless_range=t("185 m² coverage area"),
    ),
    "UAP-AC-Mesh-Pro": ap(
        "https://techspecs.ui.com/unifi/wifi/unifi-ac-mesh-pro-ap",
        "2.4 GHz and 5 GHz", 6, (450, 1300),
        ("3x3 DL MU-MIMO", "3x3 DL MU-MIMO"),
        80, "2 x 1GbE RJ45", "PoE; adapter included", 250,
        "8 dBi (2.4 GHz); 8 dBi (5 GHz)", 9,
        "343.2 x 181.2 x 60.2 mm", "-40 to 70 °C",
        ip_rating=t("IPX4"), antenna_type=t("Integrated directional antennas"),
        wireless_range=t("185 m² coverage area"),
    ),
}


class Command(BaseCommand):
    help = "Import manually verified current Ubiquiti UniFi AC/U6/U7/E7 access point specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Brand 'Ubiquiti' was not found.")
        codes = {code for item in MODELS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        updated = 0
        missing_models = []
        for model, item in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=f"Current official Tech Specs page (accessed 2026-10-12; matched to {model})",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Ubiquiti {model} official Tech Specs",
                    "region": "North America" if model == "U7-Pro-Outdoor" else "Global",
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            for code, (kind, data) in item["values"].items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from the current official Ubiquiti Tech Specs page.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(data)
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Official Tech Specs page - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if missing_models:
            raise CommandError(f"Missing published products: {', '.join(missing_models)}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS)}"))
