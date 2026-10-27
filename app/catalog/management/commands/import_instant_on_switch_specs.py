from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    Brand,
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
)


SOURCES = {
    "1830": {
        "url": "https://instant-on.hpe.com/wp-content/uploads/DS_AIO_1830SwitchSeries.pdf",
        "title": "HPE Networking Instant On Switch Series 1830 Data Sheet",
        "version": "2025-06-23",
        "published": date(2025, 6, 23),
    },
    "1930": {
        "url": "https://instant-on.hpe.com/files/DS_AIO_1930SwitchSeries.pdf",
        "title": "HPE Networking Instant On Switch Series 1930 Data Sheet",
        "version": "2025-02-11",
        "published": date(2025, 2, 11),
    },
    "1960": {
        "url": "https://instant-on.hpe.com/wp-content/uploads/DS_AIO_1960SwitchSeries.pdf",
        "title": "HPE Networking Instant On Switch Series 1960 Data Sheet",
        "version": "2025-06",
        "published": date(2025, 6, 1),
    },
}


def common_specs(interfaces, capacity, forwarding, mac, dimensions, *, memory="512 MB SDRAM", flash="256 MB flash"):
    return {
        "ethernet_interfaces": ("text", interfaces),
        "switching_capacity_gbps": ("number", capacity),
        "packet_forwarding_rate_mpps": ("number", forwarding),
        "mac_address_table": ("text", f"{mac:,} entries"),
        "packet_buffer_mb": ("number", 1.5),
        "cpu": ("text", "ARM Cortex-A9 @ 800 MHz"),
        "dram_memory": ("text", memory),
        "flash_memory": ("text", flash),
        "dimensions_mm": ("text", dimensions),
        "operating_temperature_c": ("text", "0 to 40 °C"),
        "management_methods": (
            "text",
            "Instant On cloud portal and mobile app; local web GUI; SNMP",
        ),
        "l2_features": (
            "text",
            "IEEE 802.1Q VLANs; LACP; LLDP/LLDP-MED; IGMP snooping; flow control",
        ),
    }


def poe_specs(ports, budget, *, class6=False):
    standard = "IEEE 802.3af/at/bt" if class6 else "IEEE 802.3af/at"
    return {
        "poe_configuration": (
            "text",
            f"{ports} PoE output ports; total budget {budget} W",
        ),
        "poe_standard": ("text", standard),
        "poe_ports": ("number", ports),
        "poe_budget_w": ("number", budget),
        "max_poe_per_port_w": ("number", 60 if class6 else 30),
    }


MODELS = {
    "JL810A": ("1830", common_specs("8 x 10/100/1000BASE-T RJ45", 16, 11.90, 8000, "157 x 173 x 39.1 mm"), True),
    "JL811A": ("1830", {**common_specs("8 x 10/100/1000BASE-T RJ45 (4 x PoE+)", 16, 11.90, 8000, "195.1 x 245.1 x 43.9 mm"), **poe_specs(4, 65)}, True),
    "JL812A": ("1830", common_specs("24 x 10/100/1000BASE-T RJ45; 2 x 1GbE SFP", 52, 38.68, 16000, "215.9 x 443 x 43.9 mm"), True),
    "JL813A": ("1830", {**common_specs("24 x 10/100/1000BASE-T RJ45 (12 x PoE+); 2 x 1GbE SFP", 52, 38.68, 16000, "253 x 443 x 43.9 mm"), **poe_specs(12, 195)}, False),
    "JL814A": ("1830", common_specs("48 x 10/100/1000BASE-T RJ45; 4 x 1GbE SFP", 104, 77.37, 16000, "253 x 443 x 43.9 mm"), False),
    "JL815A": ("1830", {**common_specs("48 x 10/100/1000BASE-T RJ45 (24 x PoE+); 4 x 1GbE SFP", 104, 77.37, 16000, "351 x 443 x 43.9 mm"), **poe_specs(24, 370)}, False),
    "JL680A": ("1930", common_specs("8 x 10/100/1000BASE-T RJ45; 2 x 1GbE SFP", 20, 14.88, 8000, "254 x 159.5 x 43.9 mm"), True),
    "JL681A": ("1930", {**common_specs("8 x 10/100/1000BASE-T PoE+ RJ45; 2 x 1GbE SFP", 20, 14.88, 8000, "254 x 254 x 43.9 mm"), **poe_specs(8, 124)}, True),
    "JL682A": ("1930", common_specs("24 x 10/100/1000BASE-T RJ45; 4 x 1/10GbE SFP+", 128, 95.23, 16000, "442.5 x 221.5 x 43.9 mm"), True),
    "JL684B": ("1930", {**common_specs("24 x 10/100/1000BASE-T PoE+ RJ45; 4 x 1/10GbE SFP+", 128, 95.23, 16000, "442.5 x 282.4 x 43.9 mm"), **poe_specs(24, 370)}, False),
    "JL685A": ("1930", common_specs("48 x 10/100/1000BASE-T RJ45; 4 x 1/10GbE SFP+", 176, 130.95, 16000, "442.5 x 264.7 x 43.9 mm"), True),
    "JL686B": ("1930", {**common_specs("48 x 10/100/1000BASE-T PoE+ RJ45; 4 x 1/10GbE SFP+", 176, 130.95, 16000, "442.5 x 322.6 x 43.9 mm"), **poe_specs(48, 370)}, False),
    "JL806A": ("1960", common_specs("24 x 1GbE RJ45; 2 x 10GBASE-T RJ45; 2 x 10GbE SFP+", 128, 95, 16000, "350.5 x 442.5 x 43.95 mm", memory="1 GB DDR3", flash="512 MB NAND flash"), True),
    "JL807A": ("1960", {**common_specs("24 x 1GbE RJ45 (20 x Class 4 PoE, 4 x Class 6 PoE); 2 x 10GBASE-T RJ45; 2 x 10GbE SFP+", 128, 95, 16000, "350.5 x 442.5 x 43.95 mm", memory="1 GB DDR3", flash="512 MB NAND flash"), **poe_specs(24, 370, class6=True)}, False),
    "JL808A": ("1960", common_specs("48 x 1GbE RJ45; 2 x 10GBASE-T RJ45; 2 x 10GbE SFP+", 176, 131, 16000, "350.5 x 442.5 x 43.95 mm", memory="1 GB DDR3", flash="512 MB NAND flash"), False),
    "JL809A": ("1960", {**common_specs("48 x 1GbE RJ45 (40 x Class 4 PoE, 8 x Class 6 PoE); 2 x 10GBASE-T RJ45; 2 x 10GbE SFP+", 176, 131, 16000, "402.75 x 442.5 x 43.95 mm", memory="1 GB DDR3", flash="512 MB NAND flash"), **poe_specs(48, 600, class6=True)}, False),
}

for model, (series, specs, fanless) in list(MODELS.items()):
    specs["fan_design"] = ("text", "Fanless" if fanless else "Active cooling")
    specs["stp_features"] = (
        "text",
        "IEEE 802.1D STP; IEEE 802.1w RSTP"
        + ("; IEEE 802.1s MSTP" if series in {"1930", "1960"} else ""),
    )
    if series in {"1930", "1960"}:
        specs["jumbo_frame_bytes"] = ("number", 9216)
        specs["vlan_count"] = ("number", 256)
        specs["acl_security"] = (
            "text",
            "Inbound IPv4 and MAC access control lists (ACLs)",
        )


class Command(BaseCommand):
    help = "Import manually verified HPE Networking Instant On switch datasheet specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Instant On").first()
        if not brand:
            raise CommandError("Brand 'Instant On' was not found.")
        definitions = {
            definition.code: definition
            for definition in SpecDefinition.objects.filter(
                code__in={code for _, specs, _ in MODELS.values() for code in specs}
            )
        }
        accessed = timezone.localdate()
        sources = {}
        for series, metadata in SOURCES.items():
            source, _ = SourceDocument.objects.update_or_create(
                url=metadata["url"],
                document_version=metadata["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": metadata["title"],
                    "region": "Global",
                    "published_date": metadata["published"],
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            sources[series] = source

        updated = 0
        missing_models = []
        for model, (series, values, _) in MODELS.items():
            products = Product.objects.filter(
                brand=brand,
                model=model,
                is_published=True,
            )
            if not products:
                missing_models.append(model)
                continue
            source = sources[series]
            for product in products:
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
                        "source_url": source.url[:200],
                        "source_note": f"Manually verified from latest {series} series official datasheet.",
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
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
