from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL = "https://support.dlink.com/resource/products/DGS-3620-52P/REVB/DGS-3620_DATASHEET_3.0_EN_US.PDF"
POE = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


def n(v): return "number", v
def t(v): return "text", v
def b(v=True): return "boolean", v


COMMON = {
    "mac_address_table": t("32,000 entries"),
    "packet_buffer_mb": n(2),
    "jumbo_frame_bytes": n(13000),
    "power_supply": t("100-120 V AC or 200-240 V AC, 50/60 Hz; optional RPS"),
    "fan_design": t("Smart fan cooling"),
    "management_methods": t("Web GUI; CLI; Telnet; SNMP v1/v2c/v3; RMON; sFlow; Single IP Management"),
    "vlan_count": n(4096),
    "l2_features": t("802.3ad link aggregation; ERPS; RSPAN; L2 protocol tunneling; IGMP/MLD snooping; private/Q-in-Q VLAN"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU filtering; root restriction"),
    "acl_security": t("Ingress and egress MAC/IPv4/IPv6 ACLs; 802.1X; IP-MAC-Port Binding; DHCP snooping; ARP spoofing prevention"),
    "l3_features": t("IPv4/IPv6 static and dynamic routing; PBR; VRRP; BFD; PIM; GRE/6to4/ISATAP"),
    "ip_interface_capacity": t("256 IP interfaces"),
    "routing_entry_capacity": t("12K combined IPv4/IPv6 routes; 8K combined L3 forwarding entries"),
    "ospf_support": b(), "rip_support": b(), "pbr_support": b(), "vrrp_support": b(), "multicast_routing": b(),
    "stacking": t("Physical SFP+ stacking and virtual Single IP Management"),
    "stacking_bandwidth_gbps": n(40),
    "stacking_units": n(12),
}


MODELS = {}
for suffix in ("", "/EI"):
    for stem, ports, capacity, forwarding, poe_ports in (
        ("DGS-3620-28TC", "20 x 1GbE RJ45; 4 x GbE RJ45/SFP combo; 4 x 10GbE SFP+", 128, 95.24, 0),
        ("DGS-3620-28PC", "20 x 1GbE PoE RJ45; 4 x GbE PoE/SFP combo; 4 x 10GbE SFP+", 128, 95.24, 24),
        ("DGS-3620-52T", "48 x 1GbE RJ45; 4 x 10GbE SFP+", 176, 130.95, 0),
        ("DGS-3620-52P", "48 x 1GbE PoE RJ45; 4 x 10GbE SFP+", 176, 130.95, 48),
    ):
        values = {**COMMON, "ethernet_interfaces": t(ports), "switching_capacity_gbps": n(capacity), "packet_forwarding_rate_mpps": n(forwarding)}
        if poe_ports:
            values.update({
                "poe_configuration": t(f"{poe_ports} PoE+ ports; 370 W internal / 740 W with DPS-700"),
                "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(poe_ports),
                "poe_budget_w": n(370), "max_poe_per_port_w": n(30),
            })
        MODELS[stem + suffix] = values


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-3620 base and /EI specifications."

    def add_arguments(self, parser): parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand: raise CommandError("Brand 'D-Link' was not found.")
        codes = {c for values in MODELS.values() for c in values} | POE
        defs = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if codes - defs.keys(): raise CommandError(f"Missing definitions: {sorted(codes - defs.keys())}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL, document_version="v3.0 EN US / Rev B",
            defaults={"brand": brand, "product": None, "document_type": SourceDocument.DocumentType.DATASHEET,
                      "title": "D-Link DGS-3620 Series xStack L3 Managed Stackable Gigabit Switches Datasheet",
                      "region": "Global / US", "published_date": None, "accessed_date": accessed, "active": True},
        )
        updated = na = 0; missing = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product: missing.append(model); continue
            for code, (kind, data) in values.items():
                definition = defs[code]
                defaults = {"value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "", "value_number": None,
                            "value_boolean": None, "normalized_value": str(data), "unit": definition.unit,
                            "raw_value": str(data), "source_url": URL[:200],
                            "source_note": "Manually verified from official D-Link v3.0 datasheet; /EI uses the same hardware with Enhanced Image.",
                            "verified_date": accessed}
                if kind == "number": defaults["value_number"] = Decimal(str(data))
                elif kind == "boolean": defaults["value_boolean"] = bool(data)
                else: defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(product_spec=spec, source_document=source,
                    source_location=f"Technical specifications - {model.replace('/EI', '')}",
                    defaults={"source_excerpt": f"{definition.display_name}: {data}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()})
                updated += 1
            if "PC" not in model and not model.endswith("52P") and "52P/EI" not in model:
                for code in POE:
                    definition = defs[code]
                    spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition,
                        defaults={"value_status": ProductSpec.ValueStatus.NOT_APPLICABLE, "value_text": "", "value_number": None,
                                  "value_boolean": None, "normalized_value": "", "unit": definition.unit,
                                  "raw_value": "Not a PoE model", "source_url": URL[:200],
                                  "source_note": "Official PoE table marks this model as non-PoE.", "verified_date": accessed})
                    SpecEvidence.objects.update_or_create(product_spec=spec, source_document=source,
                        source_location=f"PoE table - {model.replace('/EI', '')}",
                        defaults={"source_excerpt": "PoE: not applicable", "evidence_level": SpecEvidence.EvidenceLevel.A,
                                  "verified_at": timezone.now()})
                    na += 1
        if options["dry_run"]: transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: spec_values={updated} not_applicable={na} models={len(MODELS)-len(missing)}"))
        if missing: self.stdout.write(f"Missing models: {', '.join(missing)}")
