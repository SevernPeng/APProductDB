from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4200.pdf?cid=gwmng"


def n(value):
    return "number", value


def t(value):
    return "text", value


VALUES = {
    "switching_capacity_gbps": n(90),
    "packet_forwarding_rate_mpps": n("66.9"),
    "jumbo_frame_bytes": n(9216),
    "power_supply": t("One built-in PSU; 100-240 V AC, 50/60 Hz, 5 A maximum"),
    "fan_design": t("Fixed fans; side-to-side airflow; fan-speed control; 28.9 dB at 25 °C"),
    "poe_budget_w": n(240),
    "vlan_count": n(4093),
    "l2_features": t(
        "IEEE 802.1Q; protocol/subnet/MAC/voice/private VLANs; QinQ; GVRP/GMRP/MVRP; "
        "LACP/static LAG; IGMP/MLD snooping; LLDP-MED; QoS; RSPAN"
    ),
    "stp_features": t("STP; RSTP; MSTP (32 instances); PVST/PVST+ (32 instances); BPDU and root guard"),
    "l3_features": t(
        "IPv4/IPv6 port, subnet and VLAN static routing; RIP v1/v2; DHCPv4 relay and server"
    ),
    "routing_entry_capacity": t("32 IPv4 unicast routes; 32 IPv6 unicast routes; 32 RIP routes"),
    "rip_support": ("boolean", True),
    "max_power_consumption_w": n("281.6"),
    "dimensions_mm": t("440 x 100 x 44 mm (W x D x H)"),
    "operating_temperature_c": t("0 to 50 °C"),
}


LOCATIONS = {
    "switching_capacity_gbps": "Performance summary, p. 14",
    "packet_forwarding_rate_mpps": "Performance summary, p. 14",
    "jumbo_frame_bytes": "Other metrics, p. 15",
    "power_supply": "Physical interfaces and product illustration, pp. 11 and 14",
    "fan_design": "Physical interfaces and other metrics, pp. 14-15",
    "poe_budget_w": "Power over Ethernet, p. 14",
    "vlan_count": "Other metrics and L2 services, pp. 15-16",
    "l2_features": "Software at a glance and L2 services, pp. 2 and 15-18",
    "stp_features": "Availability and resource limits, pp. 5 and 27",
    "l3_features": "Software at a glance and routing features, pp. 2 and 7-8",
    "routing_entry_capacity": "Other metrics and resource limits, pp. 15 and 28",
    "rip_support": "Software at a glance and product summary, pp. 2 and 12",
    "max_power_consumption_w": "Power consumption, p. 29",
    "dimensions_mm": "Physical specifications, p. 29",
    "operating_temperature_c": "Environmental specifications, p. 30",
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR M4200-10MG-PoE+ specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Brand 'NETGEAR' was not found.")
        product = Product.objects.filter(
            brand=brand, model="M4200-10MG-PoE+", is_published=True
        ).first()
        if not product:
            raise CommandError("Published model 'M4200-10MG-PoE+' was not found.")

        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=VALUES)}
        if VALUES.keys() - definitions.keys():
            raise CommandError(
                f"Missing definitions: {', '.join(sorted(VALUES.keys() - definitions.keys()))}"
            )

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Current official 31-page datasheet; software release 12.0",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "NETGEAR ProSAFE Intelligent Edge Managed Switches M4200 Series Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = 0
        for code, (kind, value) in VALUES.items():
            definition = definitions[code]
            raw_value = "9KB" if code == "jumbo_frame_bytes" else str(value)
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(value),
                "unit": definition.unit,
                "raw_value": raw_value,
                "source_url": SOURCE_URL,
                "source_note": (
                    "Manually verified from NETGEAR's current official M4200 series datasheet. "
                    "The 9KB jumbo-frame value is normalized to 9216 bytes."
                ),
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
                source_location=f"{LOCATIONS[code]} - M4200-10MG-PoE+",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw_value}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models=1"))
