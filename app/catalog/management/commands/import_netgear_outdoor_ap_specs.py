from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "WAX608Y": {
        "url": "https://www.downloads.netgear.com/files/GDC/WAX608Y/WAX608Y_DS.pdf",
        "title": "NETGEAR WAX608Y Insight Managed WiFi 6 AX1800 Wireless Access Point Data Sheet",
    },
    "WAX610Y": {
        "url": "https://www.netgear.com/uk/media/WAX610-WAX610Y-DS_tcm158-90753.pdf",
        "title": "NETGEAR WAX610 and WAX610Y Insight Managed WiFi 6 AX1800 Wireless Access Points Data Sheet",
    },
    "WAX610Y_MANUAL": {
        "url": "https://www.downloads.netgear.com/files/GDC/WAX610/WAX610_WAX610Y_UM_EN.pdf",
        "title": "NETGEAR WAX610 and WAX610Y User Manual",
    },
}


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "total_spatial_streams": n(4),
    "rate_2g_mbps": n(600),
    "rate_5g_mbps": n(1200),
    "ethernet_interfaces": t("1 x 100/1000/2.5GBASE-T RJ-45"),
    "power_method": t("IEEE 802.3af/at PoE; 802.3af provides reduced throughput"),
    "ip_rating": t("IP55"),
    "antenna_type": t("Internal antennas; dual-band 2x2 MIMO"),
    "antenna_gain_dbi": t("3.6 dBi (2.4 GHz); 4.4 dBi (5 GHz)"),
    "centralized_management": t("NETGEAR Insight app and Insight Cloud Portal"),
    "mesh_support": b(),
    "fast_roaming": t("Supported; seamless roaming with Instant WiFi Mesh"),
    "wireless_security": t("WPA/WPA2/WPA3; WPA2/WPA3 Enterprise; 802.1X RADIUS; MAC access control; VLAN and guest/captive portal"),
    "max_power_consumption_w": n(16.1),
    "dimensions_mm": t("181 x 305 x 34 mm"),
    "operating_temperature_c": t("-10 to 50 °C without solar radiation"),
}


MODELS = {
    "WAX608Y": {
        **COMMON,
        "max_channel_width_mhz": n(160),
        "wireless_range": t("Up to 2,500 sq ft / 230 m²"),
    },
    "WAX610Y": {
        **COMMON,
        "max_channel_width_mhz": n(80),
        "max_clients": n(250),
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR WAX608Y and WAX610Y outdoor AP specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Brand 'NETGEAR' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        documents = {}
        for key, source_data in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"],
                document_version="Current official download",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": (
                        SourceDocument.DocumentType.SUPPORT
                        if key.endswith("MANUAL")
                        else SourceDocument.DocumentType.DATASHEET
                    ),
                    "title": source_data["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, value) in values.items():
                source_key = "WAX610Y_MANUAL" if model == "WAX610Y" and code == "max_channel_width_mhz" else model
                source_data = SOURCES[source_key]
                source = documents[source_key]
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": str(value),
                    "source_url": source_data["url"][:200],
                    "source_note": "Manually verified from the current official NETGEAR datasheet and, for WAX610Y channel width, the current official user manual.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                location = (
                    "Manage the Basic Radio Features - channel width guidance"
                    if source_key.endswith("MANUAL")
                    else f"Product comparison and technical specifications tables - {model}"
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=location,
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
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
