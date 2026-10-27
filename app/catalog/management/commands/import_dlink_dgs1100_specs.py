from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "revb": {
        "url": "https://support.dlink.com/resource/PRODUCTS/DGS-1100-SERIES/REVB/DGS-1100-SERIES_REVB_DATASHEET_3.20_EN_US.pdf",
        "title": "D-Link DGS-1100 Series Smart Managed Gigabit Switches Datasheet",
        "version": "Rev B v3.20 EN US",
        "published": date(2019, 4, 30),
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "revc": {
        "url": "https://support.dlink.com/resource/products/DGS-1100-SERIES/REVC/DGS-1100-MP-MPP_SERIES_REVC_DATASHEET_3.00_EN_US.pdf",
        "title": "D-Link DGS-1100 MP/MPP Series Datasheet",
        "version": "Rev C v3.00 EN US",
        "published": None,
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "live": {
        "url": "https://www.dlink.com/en/products/dgs-1100-10mp-10-port-gigabit-poe-smart-managed-switch",
        "title": "D-Link DGS-1100-10MP Product Page",
        "version": "Current live page",
        "published": None,
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
    },
}


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


def value(kind, data, source="revb"):
    return kind, data, source


def common_software(vlans, *, source="revb", advanced=False):
    security = (
        "D-Link Safeguard; traffic segmentation; storm control; DoS prevention; SSL; static MAC"
        if advanced
        else "Traffic segmentation; storm control; static MAC address filtering"
    )
    return {
        "jumbo_frame_bytes": value("number", 9216, source),
        "management_methods": value("text", "Web GUI; D-Link Network Assistant utility; SNMP", source),
        "vlan_count": value("number", vlans, source),
        "l2_features": value(
            "text",
            "802.1Q/port/voice/surveillance VLAN; IGMP snooping; link aggregation; "
            "loopback detection; cable diagnostics; port mirroring",
            source,
        ),
        "stp_features": value("text", "IEEE 802.1D STP; IEEE 802.1w RSTP", source),
        "acl_security": value("text", security, source),
    }


def physical(ports, capacity, forwarding, mac, buffer_mb, power, fan, max_power, dimensions, temperature, *, source="revb"):
    return {
        "ethernet_interfaces": value("text", ports, source),
        "switching_capacity_gbps": value("number", capacity, source),
        "packet_forwarding_rate_mpps": value("number", forwarding, source),
        "mac_address_table": value("text", f"{mac:,} entries", source),
        "packet_buffer_mb": value("number", buffer_mb, source),
        "power_supply": value("text", power, source),
        "fan_design": value("text", fan, source),
        "max_power_consumption_w": value("number", max_power, source),
        "dimensions_mm": value("text", dimensions, source),
        "operating_temperature_c": value("text", temperature, source),
    }


MODELS = {
    "DGS-1100-05": {
        **physical("5 x 10/100/1000BASE-T", 10, 7.4, 2000, 0.125, "100-240 V AC external adapter", "Fanless", 3.42, "100.5 x 82 x 28 mm", "0 to 40 °C"),
        **common_software(32),
    },
    "DGS-1100-08": {
        **physical("8 x 10/100/1000BASE-T", 16, 11.9, 4000, 0.188, "100-240 V AC external adapter", "Fanless", 4.94, "145 x 82 x 28 mm", "0 to 40 °C"),
        **common_software(32),
    },
    "DGS-1100-16": {
        **physical("16 x 10/100/1000BASE-T", 32, 23.81, 8000, 0.5, "100-240 V AC, 50/60 Hz internal PSU", "Fanless", 9.3, "280 x 180 x 44 mm", "-5 to 50 °C"),
        **common_software(128, advanced=True),
    },
    "DGS-1100-24": {
        **physical("24 x 10/100/1000BASE-T", 48, 35.71, 8000, 0.5, "100-240 V AC, 50/60 Hz internal PSU", "Fanless", 13.9, "280 x 180 x 44 mm", "-5 to 50 °C"),
        **common_software(128, advanced=True),
    },
    "DGS-1100-10MP": {
        **physical("8 x 10/100/1000BASE-T PoE; 2 x 1G SFP", 20, 14.88, 8000, 0.513, "100-240 V AC internal PSU", "1 smart fan", 154, "294 x 180 x 44 mm", "-10 to 55 °C", source="revc"),
        **common_software(128, source="revc", advanced=True),
        "poe_configuration": value("text", "8 PoE+ ports; 130 W total budget", "revc"),
        "poe_standard": value("text", "IEEE 802.3af/at", "revc"),
        "poe_ports": value("number", 8, "revc"),
        "poe_budget_w": value("number", 130, "revc"),
        "max_poe_per_port_w": value("number", 30, "revc"),
    },
}

# The live product page supersedes the older Rev C table for these physical values.
for code in {"max_power_consumption_w", "dimensions_mm", "operating_temperature_c", "power_supply"}:
    kind, data, _ = MODELS["DGS-1100-10MP"][code]
    MODELS["DGS-1100-10MP"][code] = value(kind, data, "live")


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-1100 specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")
        codes = {code for values in MODELS.values() for code in values} | POE_CODES
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        missing = codes - definitions.keys()
        if missing:
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        sources = {}
        for key, metadata in SOURCES.items():
            source, _ = SourceDocument.objects.update_or_create(
                url=metadata["url"],
                document_version=metadata["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": metadata["type"],
                    "title": metadata["title"],
                    "region": "Global / US",
                    "published_date": metadata["published"],
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            sources[key] = source

        updated = not_applicable = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, data, source_key) in values.items():
                definition = definitions[code]
                source = sources[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": source.url[:200],
                    "source_note": f"Manually verified from official D-Link {source.document_version} source.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Technical specifications - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

            if model != "DGS-1100-10MP":
                source = sources["revb"]
                for code in POE_CODES:
                    definition = definitions[code]
                    spec, _ = ProductSpec.objects.update_or_create(
                        product=product,
                        definition=definition,
                        defaults={
                            "value_status": ProductSpec.ValueStatus.NOT_APPLICABLE,
                            "value_text": "",
                            "value_number": None,
                            "value_boolean": None,
                            "normalized_value": "",
                            "unit": definition.unit,
                            "raw_value": "Not a PoE model",
                            "source_url": source.url[:200],
                            "source_note": "Official Rev B PoE table marks this model as non-PoE.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=source,
                        source_location=f"PoE table - {model}",
                        defaults={
                            "source_excerpt": "PoE standard, ports and budget: not applicable",
                            "evidence_level": SpecEvidence.EvidenceLevel.A,
                            "verified_at": timezone.now(),
                        },
                    )
                    not_applicable += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} not_applicable={not_applicable} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
