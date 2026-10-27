from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_SI = (
    "https://www.h3c.com/en/Products_and_Solutions/InterConnect/Switches/Products/"
    "Campus_Network/Aggregation/S6500/H3C_S6520X-SI/"
)
URL_HI = (
    "https://www.h3c.com/en/Products_and_Solutions/InterConnect/Switches/Products/"
    "Campus_Network/Aggregation/S6500/H3C_S6520X-HI/"
)
URL_6530 = (
    "https://www.h3c.com/en/Products_and_Solutions/InterConnect/Switches/Products/"
    "Campus_Network/Aggregation/S6500/H3C_S6530X_25GE/"
)


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


COMMON_FEATURES = {
    "l2_features": t(
        "Static and dynamic link aggregation; LACP; port/MAC/subnet/protocol-based VLAN; "
        "QinQ; VLAN mapping; LLDP/LLDP-MED; M-LAG; loop detection"
    ),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/RPVST+; BPDU guard; root guard"),
    "acl_security": t(
        "Layer 2-4 and time-range ACLs; ingress/egress ACLs; AAA/RADIUS/HWTACACS; "
        "802.1X and MAC authentication; IP source guard; SSH 2.0; HTTPS/SSL"
    ),
    "l3_features": t(
        "IPv4/IPv6 static routing; RIP/RIPng; OSPF/OSPFv3; IS-IS/IS-ISv6; "
        "BGP/BGP4+; ECMP; policy-based routing; VRRP"
    ),
    "ospf_support": b(True, "OSPFv1/v2/v3 supported"),
    "rip_support": b(True, "RIPv1/v2 and RIPng supported"),
    "pbr_support": b(True, "IPv4/IPv6 policy-based routing supported"),
    "multicast_routing": b(True, "PIM-DM/PIM-SM/PIM-SSM and multicast routing supported"),
}


PRODUCTS = {
    "S6520X-26C-SI": {
        "url": URL_SI,
        "title": "H3C S6520X-SI Series Multi-Gigabit 10GE Switches",
        "location": "Hardware, software, and performance specification tables",
        "values": {
            "switching_capacity_gbps": n(720, "Port switching capacity: 720 Gbps"),
            "packet_forwarding_rate_mpps": n(536, "Packet forwarding rate: 536 Mpps"),
            "packet_buffer_mb": n(3, "Buffer: 3M"),
            "dimensions_mm": t("440 x 360 x 43.6 mm (W x D x H)"),
            "max_power_consumption_w": n(113, "Maximum: AC 110 W; DC 113 W"),
            "operating_temperature_c": t("0 to 45 °C"),
            "jumbo_frame_bytes": n(10000),
            "vlan_count": n(4094),
            "ip_interface_capacity": t("1,024 VLAN interfaces"),
            "routing_entry_capacity": t("16,384 IPv4 routes; 8,192 IPv6 unicast routes"),
            "management_methods": t(
                "Console, out-of-band Ethernet and USB; CLI; H3C IMC; SNMP v1/v2c/v3; "
                "Telnet; SSH 2.0; SSL; NETCONF/YANG; gRPC; FTP; SmartMC"
            ),
            "stacking": t("H3C IRF2 over standard Ethernet ports; local or remote stacking"),
            "stacking_units": n(9),
            "stacking_bandwidth_gbps": n(160),
            **COMMON_FEATURES,
        },
    },
    "S6520X-54HF-HI": {
        "url": URL_HI,
        "title": "H3C S6520X-HI Series Advanced Aggregation 10GE Switches",
        "location": "Hardware, software, and performance specification tables",
        "values": {
            "switching_capacity_gbps": n(2160, "Port switching capacity: 2160 Gbps"),
            "packet_forwarding_rate_mpps": n(1050, "Packet forwarding rate: 1050 Mpps"),
            "packet_buffer_mb": n(12, "Packet buffer: 12M"),
            "dimensions_mm": t("440 x 360 x 43.6 mm (W x D x H)"),
            "max_power_consumption_w": n(177, "Maximum: single AC 177 W; dual AC 176 W"),
            "operating_temperature_c": t("0 to 45 °C"),
            "jumbo_frame_bytes": n(10000),
            "vlan_count": n(4094),
            "ip_interface_capacity": t("1,024 VLAN interfaces"),
            "routing_entry_capacity": t("131,072 IPv4 routes; 65,792 IPv6 unicast routes"),
            "management_methods": t(
                "Console, out-of-band Ethernet and USB; CLI; H3C IMC; SNMP v1/v2c/v3; "
                "Telnet; SSH 2.0; SSL; RESTful/RESTCONF; Python; FTP/TFTP"
            ),
            "stacking": t("H3C IRF2 over standard Ethernet ports; local or remote stacking"),
            "stacking_units": n(9),
            "stacking_bandwidth_gbps": n(480),
            **COMMON_FEATURES,
        },
    },
    "S6530X-24Y8C": {
        "url": URL_6530,
        "title": "H3C S6530X Series Advanced Aggregation 25GE Switches",
        "location": "Hardware, software, and performance specification tables",
        "values": {
            "switching_capacity_gbps": n(2800, "Port switching capacity: 2.8 Tbps"),
            "packet_forwarding_rate_mpps": n(1920),
            "packet_buffer_mb": n(36, "Packet buffer: 36M"),
            "dimensions_mm": t("440 x 400 x 44 mm (W x D x H)"),
            "max_power_consumption_w": n(193, "Maximum: single power input 188 W; dual 193 W"),
            "operating_temperature_c": t("-5 to 45 °C"),
            "jumbo_frame_bytes": n(13312),
            "vlan_count": n(4094),
            "ip_interface_capacity": t("4,094 VLAN interfaces"),
            "routing_entry_capacity": t("768K IPv4 routes; 144K IPv6 unicast routes"),
            "management_methods": t(
                "Console, out-of-band Ethernet and USB; CLI; H3C IMC; SNMP v1/v2c/v3; "
                "Telnet; SSH 2.0; SSL; NETCONF/YANG; RESTful/RESTCONF; gRPC; Cloudnet"
            ),
            "stacking": t("H3C IRF2 over standard Ethernet ports; local or remote stacking"),
            "stacking_units": n(9),
            "stacking_bandwidth_gbps": n(800),
            **COMMON_FEATURES,
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified H3C S6520X and S6530X aggregation-switch specifications."
    document_version = "Current official product page; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="H3C").first()
        if not brand:
            raise CommandError("Missing brand: H3C")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            if item["url"] in documents:
                continue
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"], document_version=self.document_version,
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": item["title"], "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing H3C product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_status = existing.value_status if existing else None
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit,
                    "raw_value": raw, "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['location']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[item["url"]],
                    source_location=f"{item['location']} - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
