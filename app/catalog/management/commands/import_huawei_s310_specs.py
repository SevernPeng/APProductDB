from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/9568f7a74e9d44c19f2d70d08ba21fd3/M3T1A590N1178058685920321688/Huawei%20ekitEngine%20S310%20Series%20Switches%20Datasheet.pdf"


def n(value):
    return "number", value


def t(value):
    return "text", value


COMMON = {
    "management_methods": t("Huawei eKit cloud app; Web system; CLI; SSHv2; SNMP v1/v2c/v3; RMON; Telnet; NETCONF/YANG"),
    "vlan_count": n(4094),
    "l2_features": t("LACP; ERPS G.8032; Smart Link; MUX VLAN; VBST; IGMPv1/v2/v3 and MLD snooping; port mirroring"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU, root and loop protection; VBST"),
    "l3_features": t("IPv4/IPv6 static routing; policy-based routing; OSPFv2/v3; VRRP; BFD"),
    "routing_entry_capacity": t("Up to 512 IPv4 FIB entries and 512 IPv6 FIB entries"),
    "stacking": t("Huawei iStack supported; multiple physical switches virtualized as one logical switch"),
    "operating_temperature_c": t("-5 to 50 °C (0-1800 m; derating above 1800 m)"),
}


MODELS = {
    "S310-24P4X": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "poe_standard": t("PoE+"),
        "poe_ports": n(24),
        "max_poe_per_port_w": n(30),
        "poe_budget_w": n(400),
        "max_power_consumption_w": n(485.91),
        "dimensions_mm": t("442 x 220 x 43.6 mm"),
    },
    "S310-48P4X": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(131),
        "poe_standard": t("PoE+"),
        "poe_ports": n(48),
        "max_poe_per_port_w": n(30),
        "poe_budget_w": n(380),
        "max_power_consumption_w": n(462.8),
        "dimensions_mm": t("442 x 220 x 43.6 mm"),
    },
    "S310-48T4X": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(131),
        "max_power_consumption_w": n(44.3),
        "dimensions_mm": t("442 x 420 x 43.6 mm"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified Huawei eKitEngine S310 switch specifications."

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
            document_version="Current official series datasheet (copyright 2023)",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "Huawei eKitEngine S310 Series Switches Datasheet",
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
                    "source_note": "Manually verified from the latest official S310 series datasheet located; unsupported table fields were intentionally left unknown.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
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
                    source_location=f"Product specifications pp. 3-6 and service features pp. 7-8 - {model}",
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
