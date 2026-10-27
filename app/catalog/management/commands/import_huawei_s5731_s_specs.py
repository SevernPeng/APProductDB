from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://e.huawei.com/en/material/networking/a910c627eaee4d0a91c4c0ede3ad041b"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "management_methods": t(
        "CLI; console; Telnet; SSH v1.5/v2.0; SNMP v1/v2c/v3; web (HTTP/HTTPS); "
        "RMON/RMON2; NETCONF/YANG; cloud management"
    ),
    "vlan_count": n(4094),
    "l2_features": t(
        "LACP/Eth-Trunk; LLDP/LLDP-MED; QinQ; MUX/Voice/Guest VLAN; GVRP; "
        "Smart Link; RRPP; SEP; ERPS G.8032; IGMP/MLD snooping; port mirroring"
    ),
    "stp_features": t(
        "STP; RSTP; MSTP (64 instances); VBST; BPDU protection; root protection; loop protection"
    ),
    "acl_security": t(
        "Basic/advanced IPv4 and IPv6 ACLs; Layer 2, user-group and user-defined ACLs; "
        "802.1X/MAC/Portal authentication; DHCP snooping; DAI; IPSG; CPU and flood attack defense"
    ),
    "ip_interface_capacity": t("1024 VLANIF interfaces"),
    "routing_entry_capacity": t("32K IPv4 routes; 8K IPv6 routes"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "stacking": t("Huawei iStack supported; up to 9 devices"),
    "stacking_bandwidth_gbps": n(80),
    "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
    "operating_temperature_c": t("-5 to 45 °C at 0-1800 m; derating above 1800 m"),
}


MODELS = {
    "S5731-S24T4X": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "max_power_consumption_w": n(114),
    },
    "S5731-S24P4X": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
        "poe_ports": n(24),
        "poe_budget_w": n(720),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(977),
    },
    "S5731-S48T4X": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(125),
        "max_power_consumption_w": n(124),
    },
    "S5731-S48P4X": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(125),
        "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
        "poe_ports": n(48),
        "poe_budget_w": n(1440),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(1750),
    },
}


LOCATIONS = {
    "switching_capacity_gbps": "Models and appearances, pp. 1-2",
    "packet_forwarding_rate_mpps": "Models and appearances, pp. 1-2",
    "poe_standard": "Power supply configurations, pp. 6-7",
    "poe_ports": "Power supply configurations, pp. 6-7",
    "poe_budget_w": "Power supply configurations and hardware specifications, pp. 6 and 20",
    "max_poe_per_port_w": "Power supply configurations, pp. 6-7",
    "management_methods": "Product features and function table, pp. 7 and 16-18",
    "vlan_count": "Function and feature metrics, p. 10",
    "l2_features": "Function and feature metrics, pp. 10-14",
    "stp_features": "Function and feature metrics, p. 12",
    "acl_security": "Function and feature metrics, pp. 15-17",
    "ip_interface_capacity": "Function and feature metrics, p. 10",
    "routing_entry_capacity": "Function and feature metrics, pp. 13-14",
    "ospf_support": "Function and feature metrics, pp. 13-14",
    "rip_support": "Function and feature metrics, pp. 13-14",
    "pbr_support": "Function and feature metrics, p. 13",
    "stacking": "Function and feature metrics, p. 15",
    "stacking_bandwidth_gbps": "Function and feature metrics, p. 15",
    "max_power_consumption_w": "Hardware specifications, p. 20",
    "dimensions_mm": "Hardware specifications, p. 18",
    "operating_temperature_c": "Hardware specifications, pp. 20-21",
}


class Command(BaseCommand):
    help = "Import manually verified Huawei CloudEngine S5731-S switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Huawei").first()
        if not brand:
            raise CommandError("Brand 'Huawei' was not found.")

        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Current official series datasheet (copyright 2024)",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "Huawei CloudEngine S5731-S Series Switches Datasheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = 0
        created = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
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
                    "source_url": SOURCE_URL,
                    "source_note": (
                        "Manually verified from Huawei's 2024 official S5731-S series datasheet. "
                        "The switching-capacity value records the device capability before the slash."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                spec, was_created = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                created += int(was_created)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{LOCATIONS[code]} - {model}",
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
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} newly_filled={created} "
                f"models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
