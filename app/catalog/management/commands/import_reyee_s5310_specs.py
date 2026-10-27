from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/9/17/Ruijie%20RG-S5310-E%20Series%20Switches%20Datasheet.pdf"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value):
    return "boolean", value


COMMON = {
    "jumbo_frame_bytes": n(9216),
    "management_methods": t(
        "CLI (console/Telnet); web management; SNMP v1/v2c/v3; RMON; Syslog; "
        "CWMP; NETCONF; gRPC; MACC; FTP/TFTP; USB backup"
    ),
    "vlan_count": n(4094),
    "l2_features": t(
        "IEEE 802.1Q; voice/super/private VLAN; GVRP; basic/selective QinQ; "
        "LACP; ERPS G.8032; LLDP/LLDP-MED; IGMP/MLD snooping"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU filter/guard; "
        "PortFast; Root Guard"
    ),
    "acl_security": t(
        "Standard/extended IP ACLs; extended MAC ACLs; expert/time-based/IPv6/global ACLs; "
        "802.1X and MAB; RADIUS/TACACS+; DHCP snooping; IP source guard; DAI; CPP/NFPP"
    ),
    "ip_interface_capacity": t("1,000 SVIs"),
    "routing_entry_capacity": t(
        "IPv4 unicast routes: 8,000 without license or 12,000 with license, shared with IPv6; "
        "IPv6 unicast routes: 4,000 shared with IPv4"
    ),
    "ospf_support": b(True),
    "rip_support": b(True),
    "pbr_support": b(True),
    "stacking": t("Ruijie VSU supported; local and remote stacking; maximum 8 members"),
    "stacking_bandwidth_gbps": n(40),
    "dimensions_mm": t("442.0 x 420.0 x 43.6 mm"),
    "operating_temperature_c": t("0 to 45 °C; derating above 1,800 m altitude"),
}


MODELS = {
    "RG-S5310-24GT4XS-E": {
        **COMMON,
        "max_power_consumption_w": n(40),
    },
    "RG-S5310-48GT4XS-E": {
        **COMMON,
        "max_power_consumption_w": n(55),
    },
    "RG-S5310-24GT4XS-P-E": {
        **COMMON,
        "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
        "poe_ports": n(24),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(810),
    },
    # The database model omits the hyphen before P; the official model is RG-S5310-48GT4XS-P-E.
    "RG-S5310-48GT4XSP-E": {
        **COMMON,
        "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
        "poe_ports": n(48),
        "poe_budget_w": n(1440),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(1570),
    },
}


def source_location(code, model):
    official_model = "RG-S5310-48GT4XS-P-E" if model == "RG-S5310-48GT4XSP-E" else model
    if code in {"dimensions_mm", "max_power_consumption_w"}:
        pages = "pp. 5-6"
    elif code in {"poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}:
        pages = "p. 6 and p. 17"
    elif code == "operating_temperature_c":
        pages = "p. 7"
    elif code in {"ip_interface_capacity", "routing_entry_capacity", "stacking", "stacking_bandwidth_gbps"}:
        pages = "p. 8"
    else:
        pages = "pp. 9-13"
    return f"Official datasheet {pages} - {official_model}"


class Command(BaseCommand):
    help = "Import manually verified Ruijie/Reyee RG-S5310-E switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Brand 'Reyee' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="V1.0 (2026-09-17)",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "Ruijie RG-S5310-E Series Switches Datasheet",
                "region": "Global",
                "published_date": date(2026, 9, 17),
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
                    "source_note": (
                        "Manually verified from the latest official RG-S5310-E series datasheet. "
                        "Switching capacity and packet forwarding rate are not listed for these copper-port "
                        "models in this edition and remain unknown."
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
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=source_location(code, model),
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
