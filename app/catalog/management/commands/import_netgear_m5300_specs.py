from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.downloads.netgear.com/files/GDC/datasheet/en/M5300.pdf"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "jumbo_frame_bytes": n(12288),
    "management_methods": t(
        "Web GUI (HTTP/HTTPS); industry-standard CLI; serial RS232 DB9 and Mini-USB console; "
        "Telnet; SSH v1/v2; SNMP v1/v2/v3; RMON; sFlow; TFTP/HTTP/SCP/SFTP"
    ),
    "vlan_count": n(4093),
    "l2_features": t(
        "IEEE 802.1Q; access/trunk ports; GVRP; private, protocol-, subnet- and MAC-based VLANs; "
        "LACP; IGMPv2/v3 and MLDv1/v2 snooping; MVR; LLDP/LLDP-MED; port mirroring"
    ),
    "stp_features": t(
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; PVSTP/PVRSTP; "
        "loop guard; root guard; BPDU guard"
    ),
    "acl_security": t(
        "IPv4/IPv6 and MAC ACLs; 802.1X; DHCP snooping; IP source guard; dynamic ARP inspection; "
        "port security; DoS protection; RADIUS/TACACS+"
    ),
    "ip_interface_capacity": t("128 routing interfaces (port or VLAN)"),
    "routing_entry_capacity": t(
        "12,256 IPv4 routes in IPv4-only SDM; or 6,112 IPv4 and 3,072 IPv6 routes in dual-stack SDM"
    ),
    "ospf_support": b(),
    "rip_support": b(),
    "stacking": t("NETGEAR Virtual Chassis stacking; chain, dual-ring or mesh; up to 8 switches"),
    "stacking_bandwidth_gbps": n(48),
    "dimensions_mm": t("440 x 391 x 43 mm"),
    "operating_temperature_c": t("0 to 50 °C"),
}


MODELS = {
    "M5300-28G": {
        **COMMON,
        "switching_capacity_gbps": n(144),
        "packet_forwarding_rate_mpps": n(107.1),
        "max_power_consumption_w": n(55),
    },
    "M5300-52G": {
        **COMMON,
        "switching_capacity_gbps": n(192),
        "packet_forwarding_rate_mpps": n(142.8),
        "max_power_consumption_w": n(79),
    },
    "M5300-28G-POE+": {
        **COMMON,
        "switching_capacity_gbps": n(144),
        "packet_forwarding_rate_mpps": n(107.1),
        "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
        "poe_ports": n(24),
        "poe_budget_w": n(720),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(535),
    },
    "M5300-52G-POE+": {
        **COMMON,
        "switching_capacity_gbps": n(192),
        "packet_forwarding_rate_mpps": n(142.8),
        "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
        "poe_ports": n(48),
        "poe_budget_w": n(1440),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(556),
    },
}


LOCATIONS = {
    "switching_capacity_gbps": "Performance summary, p. 22",
    "packet_forwarding_rate_mpps": "Performance summary, p. 22",
    "jumbo_frame_bytes": "Performance summary, pp. 23 and 34",
    "management_methods": "Management features, pp. 5, 31-33",
    "poe_standard": "Power over Ethernet, pp. 7 and 21",
    "poe_ports": "Power over Ethernet, p. 21",
    "poe_budget_w": "Power over Ethernet, p. 21",
    "max_poe_per_port_w": "Power over Ethernet, pp. 7 and 21",
    "vlan_count": "Performance summary, pp. 22-23",
    "l2_features": "Layer 2 services, pp. 23-24",
    "stp_features": "Layer 2 services, p. 24",
    "acl_security": "Security and ACL specifications, pp. 26-29 and 35",
    "ip_interface_capacity": "Performance summary, pp. 23 and 34",
    "routing_entry_capacity": "Performance summary, pp. 23 and 34",
    "ospf_support": "Layer 3 services, pp. 25-26",
    "rip_support": "Layer 3 services, p. 25",
    "stacking": "Virtual Chassis stacking, pp. 7, 12 and 22",
    "stacking_bandwidth_gbps": "Platform overview and performance, pp. 6 and 22",
    "max_power_consumption_w": "Physical specifications, p. 36",
    "dimensions_mm": "Physical specifications, p. 36",
    "operating_temperature_c": "Environmental specifications, p. 36",
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR M5300 series switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Brand 'NETGEAR' was not found.")

        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Official M5300 series datasheet, DS-M5300-2 (2015 PDF revision)",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "NETGEAR ProSAFE Next-Gen Edge Managed Switches - M5300 Series",
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
                license_note = (
                    " OSPF and RIP require the model-specific Layer 3 license upgrade."
                    if code in {"ospf_support", "rip_support"}
                    else ""
                )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": "12K" if code == "jumbo_frame_bytes" else str(value),
                    "source_url": SOURCE_URL,
                    "source_note": (
                        "Manually verified from the official M5300 series datasheet. "
                        "Maximum PoE budget includes the documented EPS4000 expansion."
                        + license_note
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
                    source_location=f"{LOCATIONS[code]} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {defaults['raw_value']}{license_note}",
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
                f"{mode}: spec_values={updated} models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
