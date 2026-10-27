from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://support.dlink.com/resource/products/dgs-3130-series/revb/DGS-3130-SERIES_REVB_DATASHEET_v1.10_WW.pdf"


def n(value): return "number", value
def t(value): return "text", value
def b(value=True): return "boolean", value


COMMON = {
    "jumbo_frame_bytes": n(9216),
    "vlan_count": n(4094),
    "l2_features": t("802.1Q; GVRP; QinQ; private, voice, MAC-, protocol- and port-based VLANs; 802.1AX/802.3ad link aggregation; ERPS v1/v2; IGMP/MLD snooping; port/RSPAN/flow mirroring"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU filtering; root guard; loop guard"),
    "acl_security": t("Multi-layer and packet-content ACLs; 802.1X/Web/MAC authentication; DHCP snooping; IP source guard; DAI; IPv6 guards/inspection; DoS prevention; RADIUS/TACACS+"),
    "ip_interface_capacity": t("128 IP interfaces"),
    "routing_entry_capacity": t("1024 IPv4/IPv6 hardware routing entries; up to 4096 shared L3 forwarding entries"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "stacking": t("Physical stacking in ring or chain topology; up to 9 30-port units or 6 54-port units"),
    "stacking_bandwidth_gbps": n(80),
}


MODELS = {
    "DGS-3130-30PS": {
        **COMMON,
        "poe_ports": n(24),
        "max_poe_per_port_w": n(30),
    },
    "DGS-3130-54TS": {**COMMON},
    "DGS-3130-54PS": {
        "jumbo_frame_bytes": n(9216),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(30),
        "vlan_count": n(4094),
        "acl_security": COMMON["acl_security"],
        "ip_interface_capacity": COMMON["ip_interface_capacity"],
        "routing_entry_capacity": COMMON["routing_entry_capacity"],
        "ospf_support": b(),
        "rip_support": b(),
        "pbr_support": b(),
        "stacking_bandwidth_gbps": n(80),
        "operating_temperature_c": t("0 to 50 °C"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-3130 Revision B specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Revision B, datasheet v1.10 WW, updated 2021-09-30",
            defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET, "title": "D-Link DGS-3130 Series Layer 3 Stackable Managed Switches", "region": "Worldwide", "published_date": None, "accessed_date": accessed, "active": True},
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
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None, "value_boolean": None, "normalized_value": str(value), "unit": definition.unit, "raw_value": "9 Kbytes" if code == "jumbo_frame_bytes" else str(value), "source_url": SOURCE_URL, "source_note": "Manually verified from the official DGS-3130 Revision B series datasheet. Maximum PoE budget includes the documented DPS-700 redundant power supply where applicable.", "verified_date": accessed}
                if kind == "number": defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean": defaults["value_boolean"] = bool(value)
                else: defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(product_spec=spec, source_document=source, source_location=f"Official datasheet pp. 1-7 - {model} - {code}", defaults={"source_excerpt": f"{definition.display_name}: {defaults['raw_value']}", "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()})
                updated += 1
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"))
        if missing_models: self.stdout.write(f"Missing models: {', '.join(missing_models)}")
