from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


FULL_L2 = t("LACP; advanced IGMP configuration and snooping; LLDP-MED; voice VLAN; port mirroring; flow and storm control; loop protection")
FULL_ACL = t("IPv4 and MAC ACLs; 802.1X; DHCP snooping and guarding; device and network isolation; port restriction and isolation")
COMPACT_L2 = t("Egress rate limiting; flow control; storm control; multicast and broadcast rate limiting; port isolation and mirroring")


MODELS = {
    "USW-Lite-8-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-lite-8-poe",
        "values": {
            "ethernet_interfaces": t("8 x 1GbE RJ45, including 4 PoE+ ports"),
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(12),
            "mac_address_table": t("8000 entries"),
            "packet_buffer_mb": n(0.5),
            "power_supply": t("External AC/DC 60 W adapter; 50-57 V DC"),
            "management_methods": t("UniFi Network management over Ethernet"),
            "poe_configuration": t("4 x PoE+ ports; 52 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(4),
            "poe_budget_w": n(52),
            "max_poe_per_port_w": n(30),
            "vlan_count": n(1000),
            "l2_features": FULL_L2,
            "stp_features": t("STP and RSTP"),
            "acl_security": FULL_ACL,
            "max_power_consumption_w": n(60),
            "dimensions_mm": t("99.6 x 163.7 x 31.7 mm"),
            "operating_temperature_c": t("-15 to 40 °C"),
        },
    },
    "USW-Lite-16-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-lite-16-poe",
        "values": {
            "ethernet_interfaces": t("16 x 1GbE RJ45, including 8 PoE+ ports"),
            "switching_capacity_gbps": n(32),
            "packet_forwarding_rate_mpps": n(24),
            "mac_address_table": t("8000 entries"),
            "packet_buffer_mb": n(0.5),
            "power_supply": t("Internal AC/DC 60 W; 100-240 V AC"),
            "management_methods": t("UniFi Network management over Ethernet"),
            "poe_configuration": t("8 x PoE+ ports; 45 W total PoE availability"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(8),
            "poe_budget_w": n(45),
            "max_poe_per_port_w": n(32),
            "vlan_count": n(1000),
            "l2_features": FULL_L2,
            "stp_features": t("STP and RSTP"),
            "acl_security": FULL_ACL,
            "max_power_consumption_w": n(60),
            "dimensions_mm": t("192 x 185 x 44 mm"),
            "operating_temperature_c": t("-15 to 40 °C"),
        },
    },
    "USW-Flex": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-flex",
        "values": {
            "ethernet_interfaces": t("5 x 1GbE RJ45: 1 PoE++ input and 4 PoE+ outputs"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7),
            "mac_address_table": t("2000 entries"),
            "power_supply": t("PoE powered; 50-57 V PoE input"),
            "management_methods": t("UniFi Network management over Ethernet"),
            "poe_configuration": t("4 x PoE+ output ports; up to 46 W total output with PoE++ or 60 W adapter input"),
            "poe_standard": t("IEEE 802.3af/at output; 802.3bt input"),
            "poe_ports": n(4),
            "poe_budget_w": n(46),
            "max_poe_per_port_w": n(25),
            "vlan_count": n(1000),
            "l2_features": COMPACT_L2,
            "acl_security": t("Port isolation"),
            "max_power_consumption_w": n(51),
            "dimensions_mm": t("122.5 x 107.1 x 28 mm"),
            "operating_temperature_c": t("-40 to 55 °C at 46 W PoE output; -40 to 65 °C at 25 W output"),
        },
    },
    "USW-Flex-Mini": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-flex-mini",
        "values": {
            "ethernet_interfaces": t("5 x 1GbE RJ45"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7),
            "mac_address_table": t("2000 entries"),
            "power_supply": t("External 5 W USB-C adapter or 44-57 V PoE input"),
            "management_methods": t("UniFi Network management over Ethernet"),
            "vlan_count": n(1000),
            "l2_features": COMPACT_L2,
            "acl_security": t("Port isolation"),
            "max_power_consumption_w": n(2.5),
            "dimensions_mm": t("107 x 70 x 21 mm"),
            "operating_temperature_c": t("-5 to 45 °C"),
        },
    },
    "USW-Flex-2.5G-8-PoE": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-flex-2-5g-8-poe",
        "values": {
            "ethernet_interfaces": t("8 x 2.5GbE RJ45 PoE++; 1 x 10GbE RJ45 PoE+++ input; 1 x 10G SFP+"),
            "switching_capacity_gbps": n(60),
            "packet_forwarding_rate_mpps": n(45),
            "mac_address_table": t("4000 entries"),
            "power_supply": t("External AC/DC adapter or PoE+++ input; adapter excluded"),
            "management_methods": t("UniFi Network management over Ethernet"),
            "poe_configuration": t("8 x PoE++ output ports; up to 196 W total output with 210 W AC adapter"),
            "poe_standard": t("IEEE 802.3af/at/bt output; PoE+++ input"),
            "poe_ports": n(8),
            "poe_budget_w": n(196),
            "max_poe_per_port_w": n(64),
            "vlan_count": n(256),
            "l2_features": t("STP/RSTP; egress rate limiting; flow and storm control; multicast and broadcast rate limiting; port isolation and mirroring; loop protection"),
            "stp_features": t("STP and RSTP"),
            "acl_security": t("Port isolation"),
            "max_power_consumption_w": n(210),
            "dimensions_mm": t("212.9 x 99.4 x 33.5 mm"),
            "operating_temperature_c": t("-20 to 45 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified current Ubiquiti UniFi compact switch specifications."

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
                    "region": "Global",
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
