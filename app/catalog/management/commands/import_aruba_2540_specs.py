from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%202540%20Switch%20Series-c05278966.pdf?contentDisposition=attachment&form=false&hf=regular&id=c05278966.pdf&isFutureVersion=true&isLinearized=false&preview=false&ver=14"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value):
    return "boolean", value


COMMON = {
    "packet_buffer_mb": n(12.38),
    "jumbo_frame_bytes": n(9220),
    "power_supply": t("Internal AC power supply; 100-127 / 200-240 V AC, 50/60 Hz"),
    "fan_design": t("Side-to-side airflow"),
    "management_methods": t("Aruba Central; Aruba AirWave; IMC; CLI; web browser; SNMP; Telnet; RMON; FTP; serial or micro-USB out-of-band management"),
    "vlan_count": n(512),
    "l2_features": t("IEEE 802.1AX/LACP; SmartLink; GVRP/MVRP; IGMP/MLD snooping; port monitoring; 4094 VLAN IDs, 512 simultaneous VLANs"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; RPVST+; BPDU protection; Root Guard"),
    "acl_security": t("IPv4/IPv6 ACLs; 802.1X, web and MAC authentication; RADIUS/TACACS+; DHCP protection; dynamic ARP protection; dynamic IP lockdown"),
    "l3_features": t("IPv4/IPv6 static routing; RIPv1/v2 and RIPng; ECMP; DHCP server/relay"),
    "routing_entry_capacity": t("2,000 IPv4 routes and 1,000 IPv6 routes; 256 static routes and 2,000 RIP routes"),
    "ospf_support": b(False),
    "rip_support": b(True),
    "pbr_support": b(False),
    "vrrp_support": b(False),
    "multicast_routing": b(False),
    "operating_temperature_c": t("0 to 45 °C up to 5,000 ft; 0 to 40 °C up to 10,000 ft"),
}


MODELS = {
    "2540 24G 4SFP+ Switch": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(95.2),
        "max_power_consumption_w": n(29.3),
        "dimensions_mm": t("442.5 x 200.2 x 43.9 mm"),
    },
    "2540 48G 4SFP+ Switch": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(112),
        "max_power_consumption_w": n(46.6),
        "dimensions_mm": t("442.5 x 246.3 x 43.9 mm"),
    },
    "2540 24G PoE+ 4SFP+ Switch": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(95.2),
        "poe_standard": t("IEEE 802.3af/at PoE+"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(445),
        "dimensions_mm": t("442.5 x 304.2 x 43.9 mm"),
    },
    "2540 48G PoE+ 4SFP+ Switch": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(112),
        "poe_standard": t("IEEE 802.3af/at PoE+"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(459),
        "dimensions_mm": t("442.5 x 304.2 x 43.9 mm"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified Aruba 2540 switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Aruba").first()
        if not brand:
            raise CommandError("Brand 'Aruba' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="QuickSpecs version 14",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "HPE Aruba Networking 2540 Switch Series QuickSpecs",
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
                    "source_note": "Manually verified from official HPE Aruba QuickSpecs version 14. Unsupported stacking and IP-interface-count fields remain unknown.",
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
                    source_location=f"Standard features pp. 1-5 and technical specifications pp. 13-17 - {model}",
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
