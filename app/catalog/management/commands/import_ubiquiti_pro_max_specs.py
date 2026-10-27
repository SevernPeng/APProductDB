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
    "l2_features": t("LACP; QoS; advanced IGMP configuration and snooping; LLDP-MED; voice VLAN; port mirroring; flow and storm control; loop protection"),
    "stp_features": t("STP and RSTP"),
    "acl_security": t("IPv4 and MAC ACLs; 802.1X; DHCP snooping and guarding; device and network isolation; port restriction and isolation"),
    "l3_features": t("DHCP server and relay; inter-VLAN routing; static routing"),
}


MODELS = {
    "USW-Pro-Max-16-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-max-16-poe",
        "values": {
            "ethernet_interfaces": t("12 x 1GbE RJ45 PoE+; 4 x 2.5GbE RJ45 PoE++; 2 x 10G SFP+"),
            "switching_capacity_gbps": n(84),
            "packet_forwarding_rate_mpps": n(62),
            "mac_address_table": t("16000 entries"),
            "packet_buffer_mb": n(1.5),
            "power_supply": t("External AC/DC 210 W adapter; 50-54 V DC"),
            "poe_configuration": t("12 x PoE+ and 4 x PoE++ ports; 180 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(16),
            "poe_budget_w": n(180),
            "max_poe_per_port_w": n(60),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "max_power_consumption_w": n(210),
            "dimensions_mm": t("325.1 x 160 x 43.7 mm"),
            "operating_temperature_c": t("-5 to 40 °C"),
        },
    },
    "USW-Pro-Max-16-PoE (180W)": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-max-16-poe",
        "values": {
            "ethernet_interfaces": t("12 x 1GbE RJ45 PoE+; 4 x 2.5GbE RJ45 PoE++; 2 x 10G SFP+"),
            "switching_capacity_gbps": n(84),
            "packet_forwarding_rate_mpps": n(62),
            "mac_address_table": t("16000 entries"),
            "packet_buffer_mb": n(1.5),
            "power_supply": t("External AC/DC 210 W adapter; 50-54 V DC"),
            "poe_configuration": t("12 x PoE+ and 4 x PoE++ ports; 180 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(16),
            "poe_budget_w": n(180),
            "max_poe_per_port_w": n(60),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "max_power_consumption_w": n(210),
            "dimensions_mm": t("325.1 x 160 x 43.7 mm"),
            "operating_temperature_c": t("-5 to 40 °C"),
        },
    },
    "USW-Pro-Max-24": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-max-24",
        "values": {
            "ethernet_interfaces": t("16 x 1GbE RJ45; 8 x 2.5GbE RJ45; 2 x 10G SFP+"),
            "switching_capacity_gbps": n(112),
            "packet_forwarding_rate_mpps": n(83),
            "mac_address_table": t("16000 entries"),
            "packet_buffer_mb": n(1.5),
            "power_supply": t("Internal AC/DC 60 W; 100-240 V AC; USP RPS DC backup input"),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "max_power_consumption_w": n(50),
            "dimensions_mm": t("442 x 325 x 44 mm"),
            "operating_temperature_c": t("-5 to 40 °C"),
        },
    },
    "USW-Pro-Max-24-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-max-24-poe",
        "values": {
            "ethernet_interfaces": t("16 x 1GbE RJ45 (8 PoE+, 8 PoE++); 8 x 2.5GbE RJ45 PoE++; 2 x 10G SFP+"),
            "switching_capacity_gbps": n(112),
            "packet_forwarding_rate_mpps": n(83),
            "mac_address_table": t("16000 entries"),
            "packet_buffer_mb": n(1.5),
            "power_supply": t("Internal AC/DC 550 W; 100-240 V AC; USP RPS DC backup input"),
            "poe_configuration": t("8 x PoE+ and 16 x PoE++ ports; 400 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(24),
            "poe_budget_w": n(400),
            "max_poe_per_port_w": n(60),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "max_power_consumption_w": n(450),
            "dimensions_mm": t("442 x 325 x 44 mm"),
            "operating_temperature_c": t("-5 to 40 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified current Ubiquiti UniFi Pro Max switch specifications."

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
                document_version=f"Current official Tech Specs page (accessed 2026-09-23; matched to {model})",
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
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
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
