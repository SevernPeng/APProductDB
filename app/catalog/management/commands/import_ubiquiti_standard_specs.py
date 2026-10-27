from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


COMMON = {
    "management_methods": t("UniFi Network management over Ethernet; AR switch management"),
    "vlan_count": n(1000),
    "l2_features": t("LACP; advanced IGMP configuration and snooping; LLDP-MED; voice VLAN; port mirroring; flow and storm control; loop protection"),
    "stp_features": t("STP and RSTP"),
    "acl_security": t("IPv4 and MAC ACLs; 802.1X; DHCP snooping and guarding; device and network isolation; port restriction and isolation"),
}


def standard_values(ports, sfp, capacity, forwarding, mac, buffer_mb, supply, power_w, dimensions, temperature):
    return {
        "ethernet_interfaces": t(f"{ports} x 1GbE RJ45; {sfp} x 1G SFP"),
        "switching_capacity_gbps": n(capacity),
        "packet_forwarding_rate_mpps": n(forwarding),
        "mac_address_table": t(f"{mac} entries"),
        "packet_buffer_mb": n(buffer_mb),
        "power_supply": t(supply),
        "max_power_consumption_w": n(power_w),
        "dimensions_mm": t(dimensions),
        "operating_temperature_c": t(temperature),
    }


MODELS = {
    "USW-16-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-16-poe",
        "values": {
            **standard_values(16, 2, 36, 27, 8000, 0.5, "Internal AC/DC 60 W; 100-240 V AC", 60, "442 x 200 x 44 mm", "-5 to 40 °C"),
            "ethernet_interfaces": t("16 x 1GbE RJ45 (8 PoE+); 2 x 1G SFP"),
            "poe_configuration": t("8 x PoE+ ports; 42 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(8),
            "poe_budget_w": n(42),
            "max_poe_per_port_w": n(32),
        },
    },
    "USW-24": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-24",
        "values": standard_values(24, 2, 52, 39, 8000, 0.5, "Internal AC/DC 36 W; 100-240 V AC", 25, "442 x 200 x 44 mm", "-5 to 45 °C"),
    },
    "USW-24-POE (95W)": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-24-poe",
        "values": {
            **standard_values(24, 2, 52, 39, 8000, 0.5, "Internal AC/DC 120 W; 100-240 V AC", 120, "442 x 200 x 44 mm", "-5 to 40 °C"),
            "ethernet_interfaces": t("24 x 1GbE RJ45 (16 PoE+); 2 x 1G SFP"),
            "poe_configuration": t("16 x PoE+ ports; 95 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(16),
            "poe_budget_w": n(95),
            "max_poe_per_port_w": n(32),
        },
    },
    "USW-48": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-48",
        "values": standard_values(48, 4, 104, 77, 16000, 1.5, "Internal AC/DC 60 W; 100-240 V AC", 40, "442 x 285 x 44 mm", "-15 to 40 °C"),
    },
    "USW-48-POE (195W)": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-48-poe",
        "values": {
            **standard_values(48, 4, 104, 77, 16000, 1.5, "Internal AC/DC 240 W; 100-240 V AC", 240, "442 x 285 x 44 mm", "-5 to 40 °C"),
            "ethernet_interfaces": t("48 x 1GbE RJ45 (32 PoE+); 4 x 1G SFP"),
            "poe_configuration": t("32 x PoE+ ports; 195 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(32),
            "poe_budget_w": n(195),
            "max_poe_per_port_w": n(32),
        },
    },
    "USW-48-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-48-poe",
        "values": {
            **standard_values(48, 4, 104, 77, 16000, 1.5, "Internal AC/DC 240 W; 100-240 V AC", 240, "442 x 285 x 44 mm", "-5 to 40 °C"),
            "ethernet_interfaces": t("48 x 1GbE RJ45 (32 PoE+); 4 x 1G SFP"),
            "poe_configuration": t("32 x PoE+ ports; 195 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(32),
            "poe_budget_w": n(195),
            "max_poe_per_port_w": n(32),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified current Ubiquiti UniFi Standard switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Brand 'Ubiquiti' was not found.")
        codes = set(COMMON) | {code for item in MODELS.values() for code in item["values"]}
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
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            for code, (kind, data) in {**COMMON, **item["values"]}.items():
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
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Overview, performance, features, and hardware - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
